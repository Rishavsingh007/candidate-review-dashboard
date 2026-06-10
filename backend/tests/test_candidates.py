import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Candidate, Score, ScoreCategory, User, UserRole  # noqa: E402
from app.seed import SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD, SEED_REVIEWER_EMAILS  # noqa: E402

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    from app.auth import hash_password
    from app.seed import SAMPLE_CANDIDATES

    admin = User(
        email=SEED_ADMIN_EMAIL,
        password_hash=hash_password(SEED_ADMIN_PASSWORD),
        role=UserRole.ADMIN.value,
    )
    db.add(admin)
    for email, password in SEED_REVIEWER_EMAILS:
        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                role=UserRole.REVIEWER.value,
            )
        )
    for data in SAMPLE_CANDIDATES:
        db.add(Candidate(**data))
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def _login(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _first_candidate_id(client, token) -> str:
    response = client.get("/candidates", headers=_auth_headers(token))
    assert response.status_code == 200
    return response.json()["items"][0]["id"]


def test_list_candidates_as_admin(client):
    token = _login(client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)
    response = client.get("/candidates", headers=_auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 10
    assert "average_score" in body["items"][0]
    assert "my_average_score" not in body["items"][0]


def test_list_candidates_as_reviewer_uses_my_average(client):
    token = _login(client, SEED_REVIEWER_EMAILS[0][0], SEED_REVIEWER_EMAILS[0][1])
    response = client.get("/candidates", headers=_auth_headers(token))
    assert response.status_code == 200
    assert "my_average_score" in response.json()["items"][0]
    assert "average_score" not in response.json()["items"][0]


def test_reviewer_cannot_see_other_reviewers_scores(client):
    reviewer1_token = _login(client, SEED_REVIEWER_EMAILS[0][0], SEED_REVIEWER_EMAILS[0][1])
    reviewer2_token = _login(client, SEED_REVIEWER_EMAILS[1][0], SEED_REVIEWER_EMAILS[1][1])
    candidate_id = _first_candidate_id(client, reviewer1_token)

    client.post(
        f"/candidates/{candidate_id}/scores",
        headers=_auth_headers(reviewer1_token),
        json={
            "category": ScoreCategory.TECHNICAL.value,
            "score": 5,
            "note": "Excellent",
        },
    )
    client.post(
        f"/candidates/{candidate_id}/scores",
        headers=_auth_headers(reviewer2_token),
        json={
            "category": ScoreCategory.TECHNICAL.value,
            "score": 3,
            "note": "Average",
        },
    )

    detail = client.get(
        f"/candidates/{candidate_id}",
        headers=_auth_headers(reviewer1_token),
    )
    assert detail.status_code == 200
    scores = detail.json()["scores"]
    assert len(scores) == 1
    assert scores[0]["score"] == 5

    admin_token = _login(client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)
    admin_detail = client.get(
        f"/candidates/{candidate_id}",
        headers=_auth_headers(admin_token),
    )
    assert len(admin_detail.json()["scores"]) == 2


def test_score_upsert_returns_201_then_200(client):
    token = _login(client, SEED_REVIEWER_EMAILS[0][0], SEED_REVIEWER_EMAILS[0][1])
    candidate_id = _first_candidate_id(client, token)
    payload = {
        "category": ScoreCategory.COMMUNICATION.value,
        "score": 4,
        "note": "Clear communicator",
    }

    first = client.post(
        f"/candidates/{candidate_id}/scores",
        headers=_auth_headers(token),
        json=payload,
    )
    assert first.status_code == 201

    payload["score"] = 5
    second = client.post(
        f"/candidates/{candidate_id}/scores",
        headers=_auth_headers(token),
        json=payload,
    )
    assert second.status_code == 200
    assert second.json()["score"] == 5

    db = TestingSessionLocal()
    try:
        count = (
            db.query(Score)
            .filter(
                Score.candidate_id == candidate_id,
                Score.category == ScoreCategory.COMMUNICATION.value,
            )
            .count()
        )
        assert count == 1
    finally:
        db.close()


def test_summary_uses_cache_unless_force(client):
    token = _login(client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)
    candidate_id = _first_candidate_id(client, token)

    first = client.post(
        f"/candidates/{candidate_id}/summary?force=false",
        headers=_auth_headers(token),
    )
    assert first.status_code == 200
    summary = first.json()["ai_summary"]
    assert summary

    second = client.post(
        f"/candidates/{candidate_id}/summary?force=false",
        headers=_auth_headers(token),
    )
    assert second.status_code == 200
    assert second.json()["ai_summary"] == summary


def test_soft_delete_archives_candidate(client):
    admin_token = _login(client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)
    candidate_id = _first_candidate_id(client, admin_token)

    delete = client.delete(
        f"/candidates/{candidate_id}",
        headers=_auth_headers(admin_token),
    )
    assert delete.status_code == 204

    detail = client.get(
        f"/candidates/{candidate_id}",
        headers=_auth_headers(admin_token),
    )
    assert detail.status_code == 404

    listing = client.get("/candidates", headers=_auth_headers(admin_token))
    assert listing.json()["total"] == 9


def test_reviewer_cannot_soft_delete(client):
    token = _login(client, SEED_REVIEWER_EMAILS[0][0], SEED_REVIEWER_EMAILS[0][1])
    candidate_id = _first_candidate_id(client, token)
    response = client.delete(
        f"/candidates/{candidate_id}",
        headers=_auth_headers(token),
    )
    assert response.status_code == 403
