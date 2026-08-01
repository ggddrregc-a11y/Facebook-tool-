from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.ai.provider import close_ai_client
from app.api import auth, comments, dashboard, health, logs, reply_test, stats, webhook
from app.config.settings import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger, setup_logging
from app.database.session import close_db, init_db, get_session_factory
from app.facebook.client import close_http_client
from app.middlewares.logging_middleware import RequestLoggingMiddleware
from app.services.auth_service import AuthService

setup_logging()
logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    settings = get_settings()
    logger.info("app_starting", model=settings.model_name)

    # Initialize database
    await init_db()

    # Ensure admin user exists
    session_factory = get_session_factory()
    async with session_factory() as session:
        auth_service = AuthService(session)
        await auth_service.ensure_admin_exists()
        await session.commit()

    logger.info("app_ready")
    yield

    # Cleanup
    await close_ai_client()
    await close_http_client()
    await close_db()
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Remix AI Auto Reply",
        description="نظام الرد التلقائي على تعليقات فيسبوك باستخدام الذكاء الاصطناعي",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Middlewares
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static files
    try:
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
    except Exception:
        pass

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "حدث خطأ داخلي في الخادم"},
        )

    # Routers
    app.include_router(health.router)
    app.include_router(webhook.router)
    app.include_router(auth.router)
    app.include_router(comments.router)
    app.include_router(stats.router)
    app.include_router(reply_test.router)
    app.include_router(logs.router)
    app.include_router(dashboard.router)

    return app


app = create_app()
