from app.models import Score, ScoreCategory, UserRole
from app.seed import (
    SEED_ADMIN_EMAIL,
    SEED_ADMIN_PASSWORD,
    SEED_REVIEWER_EMAILS,
)
from tests.conftest import (
    TestingSessionLocal,
    auth_headers,
    first_candidate_id,
    login,
)


def test_register_login_and_create_score_returns_201(client):
    register = client.post(
        "/auth/register",
        json={"email": "newreviewer@example.com", "password": "password123"},
    )
    assert register.status_code == 201
    assert register.json()["role"] == UserRole.REVIEWER.value

    token = login(client, "newreviewer@example.com", "password123")

    db = TestingSessionLocal()
    from app.models import Candidate, CandidateStatus

    candidate = Candidate(
        name="Test Candidate",
        email="test@example.com",
        role_applied="Backend Engineer",
        status=CandidateStatus.NEW.value,
        skills=["python"],
    )
    db.add(candidate)
    db.commit()
    candidate_id = candidate.id
    db.close()

    response = client.post(
        f"/candidates/{candidate_id}/scores",
        headers=auth_headers(token),
        json={
            "category": ScoreCategory.TECHNICAL.value,
            "score": 4,
            "note": "Solid skills",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["score"] == 4
    assert body["category"] == ScoreCategory.TECHNICAL.value
    assert body["note"] == "Solid skills"


def test_reviewer_cannot_see_other_reviewers_scores(seeded_client):
    reviewer1_token = login(
        seeded_client, SEED_REVIEWER_EMAILS[0][0], SEED_REVIEWER_EMAILS[0][1]
    )
    reviewer2_token = login(
        seeded_client, SEED_REVIEWER_EMAILS[1][0], SEED_REVIEWER_EMAILS[1][1]
    )
    candidate_id = first_candidate_id(seeded_client, reviewer1_token)

    seeded_client.post(
        f"/candidates/{candidate_id}/scores",
        headers=auth_headers(reviewer1_token),
        json={"category": ScoreCategory.TECHNICAL.value, "score": 5},
    )
    seeded_client.post(
        f"/candidates/{candidate_id}/scores",
        headers=auth_headers(reviewer2_token),
        json={"category": ScoreCategory.TECHNICAL.value, "score": 2},
    )

    detail = seeded_client.get(
        f"/candidates/{candidate_id}",
        headers=auth_headers(reviewer1_token),
    )
    assert detail.status_code == 200
    scores = detail.json()["scores"]
    assert len(scores) == 1
    assert scores[0]["score"] == 5
    assert "internal_notes" not in detail.json()

    admin_token = login(seeded_client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)
    admin_detail = seeded_client.get(
        f"/candidates/{candidate_id}",
        headers=auth_headers(admin_token),
    )
    assert len(admin_detail.json()["scores"]) == 2


def test_unauthenticated_request_returns_401(seeded_client):
    response = seeded_client.get("/candidates")
    assert response.status_code == 401


def test_reviewer_cannot_access_admin_route_returns_403(seeded_client):
    token = login(seeded_client, SEED_REVIEWER_EMAILS[0][0], SEED_REVIEWER_EMAILS[0][1])
    candidate_id = first_candidate_id(seeded_client, token)

    delete_response = seeded_client.delete(
        f"/candidates/{candidate_id}",
        headers=auth_headers(token),
    )
    assert delete_response.status_code == 403

    notes_response = seeded_client.patch(
        f"/candidates/{candidate_id}/internal-notes",
        headers=auth_headers(token),
        json={"internal_notes": "Should not work"},
    )
    assert notes_response.status_code == 403


def test_rescoring_same_category_updates_not_duplicates(seeded_client):
    token = login(seeded_client, SEED_REVIEWER_EMAILS[0][0], SEED_REVIEWER_EMAILS[0][1])
    candidate_id = first_candidate_id(seeded_client, token)
    payload = {
        "category": ScoreCategory.COMMUNICATION.value,
        "score": 3,
        "note": "First rating",
    }

    first = seeded_client.post(
        f"/candidates/{candidate_id}/scores",
        headers=auth_headers(token),
        json=payload,
    )
    assert first.status_code == 201

    payload["score"] = 5
    payload["note"] = "Updated rating"
    second = seeded_client.post(
        f"/candidates/{candidate_id}/scores",
        headers=auth_headers(token),
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


def test_pagination_returns_correct_page(seeded_client):
    token = login(seeded_client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)

    page1 = seeded_client.get(
        "/candidates",
        headers=auth_headers(token),
        params={"offset": 0, "limit": 5},
    )
    assert page1.status_code == 200
    body = page1.json()
    assert body["total"] == 10
    assert body["offset"] == 0
    assert body["limit"] == 5
    assert len(body["items"]) == 5

    page2 = seeded_client.get(
        "/candidates",
        headers=auth_headers(token),
        params={"offset": 5, "limit": 5},
    )
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 5

    page1_ids = {item["id"] for item in body["items"]}
    page2_ids = {item["id"] for item in page2.json()["items"]}
    assert page1_ids.isdisjoint(page2_ids)
