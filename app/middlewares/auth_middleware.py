from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger
from app.core.security import decode_access_token

logger = get_logger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول أولاً",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز المصادقة غير صالح أو منتهي",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="صلاحيات المسؤول مطلوبة",
        )
    return current_user


def get_token_from_cookie(request: Request) -> Optional[str]:
    """Extract JWT token from cookie for dashboard."""
    return request.cookies.get("access_token")


def get_dashboard_user(request: Request) -> Optional[dict]:
    """Get user from cookie for dashboard pages."""
    token = get_token_from_cookie(request)
    if not token:
        return None
    return decode_access_token(token)
