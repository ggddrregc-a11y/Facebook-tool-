from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse

logger = get_logger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.settings = get_settings()

    async def authenticate(self, username: str, password: str) -> TokenResponse:
        # Check against admin credentials from env first
        if (
            username == self.settings.admin_username
            and password == self.settings.admin_password
        ):
            token = create_access_token(
                {"sub": username, "is_admin": True},
                expires_delta=timedelta(minutes=self.settings.jwt_expire_minutes),
            )
            logger.info("admin_login_success", username=username)
            return TokenResponse(access_token=token)

        # Check database users
        user = await self.user_repo.get_by_username(username)
        if not user or not user.is_active:
            logger.warning("login_failed_user_not_found", username=username)
            raise AuthenticationException("اسم المستخدم أو كلمة المرور غير صحيحة")

        if not verify_password(password, user.hashed_password):
            logger.warning("login_failed_wrong_password", username=username)
            raise AuthenticationException("اسم المستخدم أو كلمة المرور غير صحيحة")

        token = create_access_token(
            {"sub": user.username, "is_admin": user.is_admin},
            expires_delta=timedelta(minutes=self.settings.jwt_expire_minutes),
        )
        logger.info("user_login_success", username=username)
        return TokenResponse(access_token=token)

    async def ensure_admin_exists(self) -> None:
        """Create admin user in DB if not exists."""
        existing = await self.user_repo.get_by_username(self.settings.admin_username)
        if not existing:
            hashed = hash_password(self.settings.admin_password)
            await self.user_repo.create_user(
                username=self.settings.admin_username,
                hashed_password=hashed,
                is_admin=True,
            )
            logger.info("admin_user_created", username=self.settings.admin_username)
