import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_expire_minutes
        )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        logger.warning("jwt_decode_error", error=str(e))
        return None


def verify_facebook_signature(payload: bytes, signature: str) -> bool:
    settings = get_settings()
    if not signature.startswith("sha256="):
        return False
    mac = hmac.new(
        settings.app_secret.encode("utf-8"), payload, hashlib.sha256
    )
    expected = mac.hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def generate_comment_hash(comment_text: str) -> str:
    normalized = " ".join(comment_text.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
