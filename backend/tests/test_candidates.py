from app.seed import SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD, SEED_REVIEWER_EMAILS
from tests.conftest import auth_headers, first_candidate_id, login


def test_list_candidates_as_admin(seeded_client):
    token = login(seeded_client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)
    response = seeded_client.get("/candidates", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 10
    assert "average_score" in body["items"][0]
    assert "my_average_score" not in body["items"][0]


def test_list_candidates_as_reviewer_uses_my_average(seeded_client):
    token = login(seeded_client, SEED_REVIEWER_EMAILS[0][0], SEED_REVIEWER_EMAILS[0][1])
    response = seeded_client.get("/candidates", headers=auth_headers(token))
    assert response.status_code == 200
    assert "my_average_score" in response.json()["items"][0]
    assert "average_score" not in response.json()["items"][0]


def test_summary_uses_cache_unless_force(seeded_client):
    token = login(seeded_client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)
    candidate_id = first_candidate_id(seeded_client, token)

    first = seeded_client.post(
        f"/candidates/{candidate_id}/summary?force=false",
        headers=auth_headers(token),
    )
    assert first.status_code == 200
    summary = first.json()["ai_summary"]
    assert summary

    second = seeded_client.post(
        f"/candidates/{candidate_id}/summary?force=false",
        headers=auth_headers(token),
    )
    assert second.status_code == 200
    assert second.json()["ai_summary"] == summary


def test_soft_delete_archives_candidate(seeded_client):
    admin_token = login(seeded_client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)
    candidate_id = first_candidate_id(seeded_client, admin_token)

    delete = seeded_client.delete(
        f"/candidates/{candidate_id}",
        headers=auth_headers(admin_token),
    )
    assert delete.status_code == 204

    detail = seeded_client.get(
        f"/candidates/{candidate_id}",
        headers=auth_headers(admin_token),
    )
    assert detail.status_code == 404

    listing = seeded_client.get("/candidates", headers=auth_headers(admin_token))
    assert listing.json()["total"] == 9


def test_reviewer_cannot_list_archived_candidates(seeded_client):
    admin_token = login(seeded_client, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD)
    reviewer_token = login(
        seeded_client, SEED_REVIEWER_EMAILS[0][0], SEED_REVIEWER_EMAILS[0][1]
    )
    candidate_id = first_candidate_id(seeded_client, admin_token)

    delete = seeded_client.delete(
        f"/candidates/{candidate_id}",
        headers=auth_headers(admin_token),
    )
    assert delete.status_code == 204

    reviewer_list = seeded_client.get(
        "/candidates",
        headers=auth_headers(reviewer_token),
        params={"status": "archived"},
    )
    assert reviewer_list.status_code == 200
    assert reviewer_list.json()["total"] == 0
    assert reviewer_list.json()["items"] == []

    admin_list = seeded_client.get(
        "/candidates",
        headers=auth_headers(admin_token),
        params={"status": "archived"},
    )
    assert admin_list.status_code == 200
    assert admin_list.json()["total"] >= 1
