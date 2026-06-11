import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret")

from app.auth import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Candidate, User, UserRole
from app.seed import (
    SAMPLE_CANDIDATES,
    SEED_ADMIN_EMAIL,
    SEED_ADMIN_PASSWORD,
    SEED_REVIEWER_EMAILS,
)

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seeded_client(client):
    db = TestingSessionLocal()
    db.add(
        User(
            email=SEED_ADMIN_EMAIL,
            password_hash=hash_password(SEED_ADMIN_PASSWORD),
            role=UserRole.ADMIN.value,
        )
    )
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
    return client


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def first_candidate_id(client: TestClient, token: str) -> str:
    response = client.get("/candidates", headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()["items"][0]["id"]
