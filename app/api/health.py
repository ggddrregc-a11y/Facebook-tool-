from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.config.settings import get_settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    model: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        model=settings.model_name,
    )
