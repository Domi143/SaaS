import pytest


async def _register(client, email: str):
    await client.get("/login")
    csrf = client.cookies.get("csrf_token")
    r = await client.post(
        "/register",
        data={"email": email, "password": "password123", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)


@pytest.mark.asyncio
async def test_workspace_crud_isolated(client):
    # user A
    await _register(client, "a@example.com")
    csrf = client.cookies.get("csrf_token")
    r = await client.post("/app/workspaces", data={"name": "A-WS", "csrf_token": csrf})
    assert r.status_code in (200, 204)
    # follow redirect header
    ws_url = r.headers.get("HX-Redirect")
    assert ws_url and ws_url.startswith("/app/workspaces/")

    r = await client.get(ws_url)
    assert r.status_code == 200
    assert "A-WS" in r.text

    # logout
    csrf = client.cookies.get("csrf_token")
    r = await client.post("/logout", data={"csrf_token": csrf}, follow_redirects=False)
    assert r.status_code in (302, 303)

    # user B
    await _register(client, "b@example.com")
    r = await client.get(ws_url)
    assert r.status_code == 404

