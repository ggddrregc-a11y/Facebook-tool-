"""API routes for AI post management."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.database.session import get_db
from app.middlewares.auth_middleware import require_admin
from app.repositories.post_repository import PostRepository
from app.schemas.post import (
    PostGenerateRequest,
    PostApproveRequest,
    PostRejectRequest,
    PostUpdateRequest,
    PostResponse,
    PostListResponse,
    PostStatsResponse,
)
from app.services.post_service import PostService

router = APIRouter(prefix="/api/posts", tags=["Posts"])


@router.get("", response_model=PostListResponse)
async def list_posts(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    repo = PostRepository(db)
    offset = (page - 1) * per_page
    posts = await repo.list_posts(status=status, limit=per_page, offset=offset)
    total = await repo.count(status=status)
    return PostListResponse(
        posts=[PostResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("/generate", response_model=PostResponse, status_code=201)
async def generate_post(
    request: PostGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    try:
        service = PostService(db)
        post = await service.generate_new_post(
            topic=request.topic,
            extra_instructions=request.extra_instructions,
            schedule_at=request.schedule_at,
            auto_publish=request.auto_publish,
            generate_image=request.generate_image,
        )
        return PostResponse.model_validate(post)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=PostStatsResponse)
async def get_post_stats(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    service = PostService(db)
    stats = await service.get_post_stats()
    return PostStatsResponse(**stats)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")
    return PostResponse.model_validate(post)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    request: PostUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    try:
        service = PostService(db)
        if request.content:
            post = await service.update_post_content(post_id, request.content, request.topic)
        else:
            repo = PostRepository(db)
            post = await repo.get_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="المنشور غير موجود")
        return PostResponse.model_validate(post)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{post_id}/approve", response_model=PostResponse)
async def approve_post(
    post_id: int,
    request: PostApproveRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin),
):
    try:
        service = PostService(db)
        post = await service.approve_post(
            post_id,
            approved_by=user.get("username", "admin"),
            publish_now=request.publish_now,
            schedule_at=request.schedule_at,
        )
        return PostResponse.model_validate(post)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{post_id}/reject", response_model=PostResponse)
async def reject_post(
    post_id: int,
    request: PostRejectRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    try:
        service = PostService(db)
        post = await service.reject_post(post_id, reason=request.reason)
        return PostResponse.model_validate(post)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{post_id}/publish", response_model=PostResponse)
async def publish_post_now(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    try:
        service = PostService(db)
        post = await service.publish_post_now(post_id)
        return PostResponse.model_validate(post)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{post_id}/insights", response_model=PostResponse)
async def refresh_insights(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    service = PostService(db)
    post = await service.refresh_insights(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")
    return PostResponse.model_validate(post)


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    try:
        service = PostService(db)
        await service.delete_post(post_id)
        return {"message": "تم حذف المنشور بنجاح"}
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
