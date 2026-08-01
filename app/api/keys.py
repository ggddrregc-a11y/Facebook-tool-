"""API routes for Grok API key management and status."""

from fastapi import APIRouter, Depends

from app.ai.provider import get_keys_status
from app.middlewares.auth_middleware import require_admin
from app.schemas.post import KeyStatusItem, KeysStatusResponse

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


@router.get("", response_model=KeysStatusResponse)
async def get_keys_status_route(_: dict = Depends(require_admin)) -> KeysStatusResponse:
    """Return status of all configured Grok API keys."""
    statuses = get_keys_status()
    items = [KeyStatusItem(**s) for s in statuses]
    active = sum(1 for s in items if s.active)
    return KeysStatusResponse(
        keys=items,
        total_keys=len(items),
        active_keys=active,
    )
