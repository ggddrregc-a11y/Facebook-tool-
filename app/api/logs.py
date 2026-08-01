from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.middlewares.auth_middleware import require_admin
from app.repositories.log_repository import LogRepository
from app.schemas.stats import LogListResponse, LogResponse

router = APIRouter(prefix="/api", tags=["Logs"])


@router.get("/logs", response_model=LogListResponse)
async def get_logs(
    level: str = Query(None, description="مستوى السجل"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
) -> LogListResponse:
    repo = LogRepository(db)
    total, items = await repo.get_paginated(page=page, per_page=per_page, level=level)
    return LogListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[
            LogResponse(
                id=log.id,
                level=log.level,
                event=log.event,
                message=log.message,
                source=log.source,
                comment_id=log.comment_id,
                extra_data=log.extra_data,
                created_at=log.created_at.isoformat(),
            )
            for log in items
        ],
    )
