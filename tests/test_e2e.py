import pytest
import httpx
import uuid

BASE_URL = "http://localhost:8080"
HEADERS = {"Authorization": "Bearer secret-token"}


@pytest.mark.e2e
def test_e2e_health():
    response = httpx.get(f"{BASE_URL}/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["api"] == "ok"
    assert data["db"] == "ok"


@pytest.mark.e2e
def test_e2e_full_flow():
    suffix = str(uuid.uuid4())[:8]
    team_name = f"e2e_team_{suffix}"
    u1 = f"u_e2e_1_{suffix}"
    u2 = f"u_e2e_2_{suffix}"
    pr_id = f"pr_e2e_{suffix}"

    # 1. Create Team
    response = httpx.post(
        f"{BASE_URL}/team/add",
        json={
            "team_name": team_name,
            "members": [
                {"user_id": u1, "username": "E2E_User1", "is_active": True},
                {"user_id": u2, "username": "E2E_User2", "is_active": True},
            ],
        },
        headers=HEADERS,
    )
    assert response.status_code == 201

    # 2. Create PR
    response = httpx.post(
        f"{BASE_URL}/pullRequest/create",
        json={"pull_request_id": pr_id, "pull_request_name": "E2E PR", "author_id": u1},
        headers=HEADERS,
    )
    assert response.status_code == 201
    data = response.json()
    assert u2 in data["pr"]["assigned_reviewers"]

    # 3. Merge PR
    response = httpx.post(f"{BASE_URL}/pullRequest/merge", json={"pull_request_id": pr_id}, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["pr"]["status"] == "MERGED"
