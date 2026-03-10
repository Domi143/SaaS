from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.webhook_handler import (
    extract_subscription_fields,
    parse_paddle_event,
    verify_paddle_signature,
)
from app.db.session import get_db
from app.services.billing_service import BillingService


router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def paddle_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> None:
    raw = await request.body()
    sig = request.headers.get("Paddle-Signature") or request.headers.get("paddle-signature")
    verify_paddle_signature(raw, sig)

    payload: dict[str, Any] = json.loads(raw.decode("utf-8"))
    event = parse_paddle_event(payload)

    service = BillingService(db)
    event_id = event["event_id"]
    if not event_id or event_id == "None":
        # We require a stable event id for idempotency
        return
    is_new = await service.mark_webhook_processed("paddle", event_id)
    if not is_new:
        return

    fields = extract_subscription_fields(event)
    # user mapping: in this MVP, we expect you to pass user_id in the event data if configured in checkout passthrough.
    user_id = None
    data = event.get("data") or {}
    if isinstance(data, dict) and "passthrough" in data:
        try:
            passthrough = data["passthrough"]
            if isinstance(passthrough, str):
                pt = json.loads(passthrough)
                user_id = int(pt.get("user_id")) if pt.get("user_id") else None
            elif isinstance(passthrough, dict):
                user_id = int(passthrough.get("user_id")) if passthrough.get("user_id") else None
        except Exception:
            user_id = None

    await service.apply_subscription_update(
        user_id=user_id,
        paddle_customer_id=fields["paddle_customer_id"],
        paddle_subscription_id=fields["paddle_subscription_id"],
        status=fields["status"],
        plan_name=fields["plan_name"],
        current_period_end=fields["current_period_end"],
    )

