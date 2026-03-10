import hmac
import json
from hashlib import sha256

import pytest


@pytest.mark.asyncio
async def test_webhook_idempotency(client, monkeypatch):
    # Configure webhook secret for test app settings.
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "paddle_webhook_secret", "testsecret")
    monkeypatch.setattr(cfg.settings, "paddle_price_id_plus", "price_plus")

    # Create a user so FK constraints are satisfied (user id should be 1 in fresh DB).
    await client.get("/login")
    csrf = client.cookies.get("csrf_token")
    r = await client.post(
        "/register",
        data={"email": "bill@example.com", "password": "password123", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)

    payload = {
        "event_id": "evt_123",
        "event_type": "subscription.updated",
        "data": {
            "subscription_id": "sub_abc",
            "customer_id": "cus_xyz",
            "status": "active",
            "items": [{"price_id": "price_plus"}],
            "passthrough": json.dumps({"user_id": 1}),
        },
    }
    raw = json.dumps(payload).encode("utf-8")
    sig = hmac.new(b"testsecret", raw, sha256).hexdigest()

    r1 = await client.post("/billing/webhook", content=raw, headers={"Paddle-Signature": sig})
    assert r1.status_code == 204

    # same event again -> still 204, but should be ignored due to idempotency
    r2 = await client.post("/billing/webhook", content=raw, headers={"Paddle-Signature": sig})
    assert r2.status_code == 204

