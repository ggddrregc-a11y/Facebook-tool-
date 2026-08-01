"""Background scheduler that publishes due posts every N seconds."""

import asyncio
import sys

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.database.session import get_session_factory
from app.services.post_service import PostService

logger = get_logger(__name__)

_scheduler_task: asyncio.Task | None = None


async def _run_scheduler() -> None:
    settings = get_settings()
    interval = settings.post_scheduler_interval_seconds
    logger.info("post_scheduler_started", interval_seconds=interval)

    while True:
        try:
            await asyncio.sleep(interval)
            session_factory = get_session_factory()
            async with session_factory() as session:
                service = PostService(session)
                await service.process_due_posts()
                await session.commit()
        except asyncio.CancelledError:
            logger.info("post_scheduler_stopped")
            break
        except Exception as e:
            print(f"[SCHEDULER ERROR] {e}", file=sys.stderr, flush=True)
            logger.error("post_scheduler_error", error=str(e))


def start_post_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_run_scheduler())
        logger.info("post_scheduler_task_created")


async def stop_post_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
    _scheduler_task = None
