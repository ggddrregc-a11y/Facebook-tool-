from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.middlewares.auth_middleware import get_dashboard_user
from app.repositories.comment_repository import CommentRepository
from app.repositories.log_repository import LogRepository
from app.repositories.post_repository import PostRepository
from app.schemas.comment import CommentSearchParams
from app.services.stats_service import StatsService

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


def _require_dashboard_auth(request: Request):
    user = get_dashboard_user(request)
    if not user:
        return None
    return user


@router.get("/", response_class=HTMLResponse)
async def dashboard_root(request: Request):
    return RedirectResponse(url="/dashboard")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_dashboard_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = _require_dashboard_auth(request)
    if not user:
        return RedirectResponse(url="/login")

    from app.database.session import get_session_factory
    session_factory = get_session_factory()
    async with session_factory() as db:
        try:
            stats_service = StatsService(db)
            stats = await stats_service.get_dashboard_stats()

            comment_repo = CommentRepository(db)
            recent_comments = await comment_repo.get_recent(limit=10)

            post_repo = PostRepository(db)
            post_counts = await post_repo.count_by_status()

            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "user": user,
                    "stats": stats,
                    "recent_comments": recent_comments,
                    "post_counts": post_counts,
                },
            )
        except Exception:
            await db.rollback()
            raise


@router.get("/dashboard/comments", response_class=HTMLResponse)
async def comments_page(
    request: Request,
    q: str = Query(None),
    emotion: str = Query(None),
    reply_sent: bool = Query(None),
    is_spam: bool = Query(None),
    page: int = Query(1, ge=1),
):
    user = _require_dashboard_auth(request)
    if not user:
        return RedirectResponse(url="/login")

    from app.database.session import get_session_factory
    session_factory = get_session_factory()
    async with session_factory() as db:
        params = CommentSearchParams(
            q=q,
            emotion=emotion,
            reply_sent=reply_sent,
            is_spam=is_spam,
            page=page,
            per_page=20,
        )
        repo = CommentRepository(db)
        total, items = await repo.search(params)
        total_pages = (total + 19) // 20

        return templates.TemplateResponse(
            "comments.html",
            {
                "request": request,
                "user": user,
                "comments": items,
                "total": total,
                "page": page,
                "total_pages": total_pages,
                "q": q or "",
                "emotion": emotion or "",
            },
        )


@router.get("/dashboard/logs", response_class=HTMLResponse)
async def logs_page(
    request: Request,
    level: str = Query(None),
    page: int = Query(1, ge=1),
):
    user = _require_dashboard_auth(request)
    if not user:
        return RedirectResponse(url="/login")

    from app.database.session import get_session_factory
    session_factory = get_session_factory()
    async with session_factory() as db:
        repo = LogRepository(db)
        total, items = await repo.get_paginated(page=page, per_page=30, level=level)
        total_pages = (total + 29) // 30

        return templates.TemplateResponse(
            "logs.html",
            {
                "request": request,
                "user": user,
                "logs": items,
                "total": total,
                "page": page,
                "total_pages": total_pages,
                "level": level or "",
            },
        )


@router.get("/dashboard/test", response_class=HTMLResponse)
async def test_page(request: Request):
    user = _require_dashboard_auth(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("test.html", {"request": request, "user": user})


@router.get("/dashboard/posts", response_class=HTMLResponse)
async def posts_page(
    request: Request,
    status: str = Query(None),
    page: int = Query(1, ge=1),
):
    user = _require_dashboard_auth(request)
    if not user:
        return RedirectResponse(url="/login")

    from app.database.session import get_session_factory
    session_factory = get_session_factory()
    async with session_factory() as db:
        repo = PostRepository(db)
        per_page = 20
        offset = (page - 1) * per_page
        posts = await repo.list_posts(status=status or None, limit=per_page, offset=offset)
        total = await repo.count(status=status or None)
        total_pages = (total + per_page - 1) // per_page
        counts = await repo.count_by_status()

        return templates.TemplateResponse(
            "posts.html",
            {
                "request": request,
                "user": user,
                "posts": posts,
                "total": total,
                "page": page,
                "total_pages": total_pages,
                "current_status": status or "",
                "counts": counts,
            },
        )


@router.get("/dashboard/keys", response_class=HTMLResponse)
async def keys_page(request: Request):
    user = _require_dashboard_auth(request)
    if not user:
        return RedirectResponse(url="/login")

    from app.ai.provider import get_keys_status
    key_statuses = get_keys_status()

    return templates.TemplateResponse(
        "keys.html",
        {
            "request": request,
            "user": user,
            "key_statuses": key_statuses,
        },
    )
