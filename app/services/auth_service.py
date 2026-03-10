from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password, verify_password
from app.auth.tokens import create_access_token, create_refresh_token
from app.core.plans import get_plan_limits
from app.core.config import settings
from app.models import BillingCustomer, User


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register_user(self, email: str, password: str) -> User:
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ValueError("User already exists")

        user = User(email=email, hashed_password=hash_password(password))
        self.db.add(user)
        await self.db.flush()

        limits = get_plan_limits(settings.default_plan_name)
        billing = BillingCustomer(
            user_id=user.id,
            plan_name=limits.name,
            subscription_status="inactive",
            storage_limit_bytes=limits.storage_limit_bytes,
        )
        self.db.add(billing)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_token_pair(self, user_id: int) -> tuple[str, str]:
        access = create_access_token(str(user_id))
        refresh = create_refresh_token(str(user_id))
        return access, refresh

