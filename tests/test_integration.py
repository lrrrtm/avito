import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_integration_full_flow(client: AsyncClient):
    uid = str(uuid.uuid4())[:8]
    team_name = f"int_team_{uid}"
    u1 = f"u1_{uid}"
    u2 = f"u2_{uid}"
    pr_id = f"pr_{uid}"

    # 1. Create team
    response = await client.post(
        "/team/add",
        json={
            "team_name": team_name,
            "members": [
                {"user_id": u1, "username": "User1", "is_active": True},
                {"user_id": u2, "username": "User2", "is_active": True},
            ],
        },
    )
    assert response.status_code == 201

    # 2. Create PR by User1
    response = await client.post(
        "/pullRequest/create", json={"pull_request_id": pr_id, "pull_request_name": "Integration PR", "author_id": u1}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["pr"]["status"] == "OPEN"
    reviewers = data["pr"]["assigned_reviewers"]
    assert u2 in reviewers

    # 3. Verify user reviews
    response = await client.get("/users/getReview", params={"user_id": u2})
    assert response.status_code == 200
    prs = response.json()["pull_requests"]
    assert any(pr["pull_request_id"] == pr_id for pr in prs)

    # 4. Merge PR
    response = await client.post("/pullRequest/merge", json={"pull_request_id": pr_id})
    assert response.status_code == 200
    assert response.json()["pr"]["status"] == "MERGED"


@pytest.mark.asyncio
async def test_integration_reassign(client: AsyncClient):
    uid = str(uuid.uuid4())[:8]
    team_name = f"reassign_team_{uid}"
    u1 = f"u1_{uid}"
    u2 = f"u2_{uid}"
    u3 = f"u3_{uid}"
    u4 = f"u4_{uid}"
    pr_id = f"pr_reassign_{uid}"

    # 1. Create team
    members = [
        {"user_id": u1, "username": "R1", "is_active": True},
        {"user_id": u2, "username": "R2", "is_active": True},
        {"user_id": u3, "username": "R3", "is_active": True},
        {"user_id": u4, "username": "R4", "is_active": True},
    ]
    await client.post("/team/add", json={"team_name": team_name, "members": members})

    # 2. Create PR
    response = await client.post(
        "/pullRequest/create", json={"pull_request_id": pr_id, "pull_request_name": "Reassign PR", "author_id": u1}
    )
    reviewers = response.json()["pr"]["assigned_reviewers"]
    old_reviewer = reviewers[0]

    # 3. Reassign
    response = await client.post(
        "/pullRequest/reassign", json={"pull_request_id": pr_id, "old_reviewer_id": old_reviewer}
    )
    assert response.status_code == 200
    new_reviewer = response.json()["replaced_by"]
    assert new_reviewer != old_reviewer
    assert new_reviewer in [u2, u3, u4]


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health/")
    assert response.status_code == 200
    assert response.json()["db"] == "ok"


@pytest.mark.asyncio
async def test_integration_mass_deactivate(client: AsyncClient):
    uid = str(uuid.uuid4())[:8]
    team_name = f"deact_team_{uid}"
    u1 = f"u1_{uid}"
    u2 = f"u2_{uid}"
    u3 = f"u3_{uid}"
    pr_id = f"pr_deact_{uid}"

    members = [
        {"user_id": u1, "username": "Author", "is_active": True},
        {"user_id": u2, "username": "Reviewer", "is_active": True},
        {"user_id": u3, "username": "Replacement", "is_active": True},
    ]
    await client.post("/team/add", json={"team_name": team_name, "members": members})

    response = await client.post(
        "/pullRequest/create", json={"pull_request_id": pr_id, "pull_request_name": "Deactivation PR", "author_id": u1}
    )
    assert response.status_code == 201
    reviewers = response.json()["pr"]["assigned_reviewers"]

    target_user = reviewers[0]

    response = await client.post("/team/deactivate", json={"team_name": team_name, "user_ids": [target_user]})
    assert response.status_code == 200

    response = await client.get("/team/get", params={"team_name": team_name})
    team_data = response.json()
    for member in team_data["members"]:
        if member["user_id"] == target_user:
            assert member["is_active"] == False
        else:
            assert member["is_active"] == True

    expected_replacement = u3 if target_user == u2 else u2

    response = await client.get("/users/getReview", params={"user_id": expected_replacement})
    prs = response.json()["pull_requests"]
    assert any(pr["pull_request_id"] == pr_id for pr in prs)
