from __future__ import annotations

import hmac
import json
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from fastapi import HTTPException, Request, status

from app.core.config import settings


def verify_paddle_signature(raw_body: bytes, signature_header: str | None) -> None:
    """
    Production note:
    Paddle's webhook signature format depends on the product version and settings.
    This MVP implements a strict HMAC-SHA256(raw_body, webhook_secret) comparison.
    If your Paddle account uses a different signature scheme/headers, adapt here.
    """
    secret = settings.paddle_webhook_secret
    if not secret:
        raise HTTPException(status_code=500, detail="PADDLE_WEBHOOK_SECRET not configured")
    if not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")

    expected = hmac.new(secret.encode("utf-8"), raw_body, sha256).hexdigest()
    provided = signature_header.strip()
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")


def parse_paddle_event(payload: dict[str, Any]) -> dict[str, Any]:
    # Normalize a minimal subset we need. Adapt to your Paddle event shape.
    event_id = payload.get("event_id") or payload.get("id") or payload.get("alert_id")
    event_type = payload.get("event_type") or payload.get("event_name") or payload.get("alert_name")
    data = payload.get("data") or payload

    return {"event_id": str(event_id), "event_type": str(event_type), "data": data}


def extract_subscription_fields(event: dict[str, Any]) -> dict[str, Any]:
    data = event["data"] or {}
    # These keys vary by Paddle product. Keep flexible and prefer env mapping later.
    paddle_customer_id = data.get("customer_id") or data.get("paddle_customer_id")
    paddle_subscription_id = data.get("subscription_id") or data.get("paddle_subscription_id")
    status = data.get("status") or data.get("subscription_status") or "unknown"

    items = data.get("items") or []
    price_id = None
    if isinstance(items, list) and items:
        price_id = items[0].get("price_id") or items[0].get("price") or items[0].get("product_id")
    price_id = data.get("price_id") or price_id

    plan_name = _map_price_to_plan(price_id)
    current_period_end = _parse_dt(data.get("current_period_end") or data.get("next_bill_date"))

    return {
        "paddle_customer_id": paddle_customer_id,
        "paddle_subscription_id": paddle_subscription_id,
        "status": str(status),
        "plan_name": plan_name,
        "current_period_end": current_period_end,
    }


def _map_price_to_plan(price_id: str | None) -> str:
    if not price_id:
        return settings.default_plan_name
    if settings.paddle_price_id_pro and price_id == settings.paddle_price_id_pro:
        return "pro"
    if settings.paddle_price_id_plus and price_id == settings.paddle_price_id_plus:
        return "plus"
    if settings.paddle_price_id_free and price_id == settings.paddle_price_id_free:
        return "free"
    return settings.default_plan_name


def _parse_dt(val: Any) -> datetime | None:
    if not val:
        return None
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc)
    if isinstance(val, str):
        try:
            # Accept ISO8601-ish
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None

