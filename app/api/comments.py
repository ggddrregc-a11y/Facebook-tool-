from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.middlewares.auth_middleware import require_admin
from app.repositories.comment_repository import CommentRepository
from app.schemas.comment import CommentListResponse, CommentSearchParams

router = APIRouter(prefix="/api", tags=["Comments"])


@router.get("/comments", response_model=CommentListResponse)
async def get_comments(
    q: str = Query(None, description="بحث نصي"),
    emotion: str = Query(None, description="تصفية حسب المشاعر"),
    reply_sent: bool = Query(None, description="تصفية حسب حالة الرد"),
    is_spam: bool = Query(None, description="تصفية حسب السبام"),
    page: int = Query(1, ge=1, description="رقم الصفحة"),
    per_page: int = Query(20, ge=1, le=100, description="عدد النتائج في الصفحة"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
) -> CommentListResponse:
    params = CommentSearchParams(
        q=q,
        emotion=emotion,
        reply_sent=reply_sent,
        is_spam=is_spam,
        page=page,
        per_page=per_page,
    )
    repo = CommentRepository(db)
    total, items = await repo.search(params)
    return CommentListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=items,
    )
