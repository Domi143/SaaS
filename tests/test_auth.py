import pytest


@pytest.mark.asyncio
async def test_register_and_login_web(client):
    # prime csrf
    r = await client.get("/login")
    assert r.status_code == 200
    assert "csrf_token" in client.cookies
    csrf = client.cookies.get("csrf_token")

    r = await client.post(
        "/register",
        data={"email": "a@example.com", "password": "password123", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)
    assert client.cookies.get("access_token")

    r = await client.get("/app/dashboard")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_protected_requires_login(client):
    r = await client.get("/app/dashboard")
    assert r.status_code == 401

