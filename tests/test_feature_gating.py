import pytest


@pytest.mark.asyncio
async def test_free_plan_workspace_limit(client):
    await client.get("/login")
    csrf = client.cookies.get("csrf_token")
    r = await client.post(
        "/register",
        data={"email": "limit@example.com", "password": "password123", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)

    csrf = client.cookies.get("csrf_token")
    r1 = await client.post("/app/workspaces", data={"name": "WS1", "csrf_token": csrf})
    assert r1.status_code in (200, 204)

    csrf = client.cookies.get("csrf_token")
    r2 = await client.post("/app/workspaces", data={"name": "WS2", "csrf_token": csrf})
    assert r2.status_code == 403

