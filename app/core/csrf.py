from __future__ import annotations

import secrets

from fastapi import HTTPException, Request, status


CSRF_COOKIE_NAME = "csrf_token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def get_csrf_token_from_request(request: Request) -> str | None:
    # Prefer header (HTMX) then form then query (fallback)
    header_val = request.headers.get(CSRF_HEADER)
    if header_val:
        return header_val
    return None


async def verify_csrf(request: Request) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    if not cookie_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF cookie missing")

    provided = request.headers.get(CSRF_HEADER)
    if not provided:
        form = await request.form()
        provided = form.get(CSRF_FORM_FIELD)  # type: ignore[assignment]

    if not provided or provided != cookie_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF failed")

