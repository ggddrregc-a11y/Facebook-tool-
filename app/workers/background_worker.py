import asyncio
import sys
from typing import Optional, Set

from app.core.logging import get_logger
from app.database.session import get_session_factory
from app.services.comment_pipeline import CommentPipeline

logger = get_logger(__name__)

# Strong references to running tasks — prevents Python GC from silently
# discarding asyncio.Task objects before they complete (Python 3.11+).
_background_tasks: Set[asyncio.Task] = set()


async def process_comment_task(
    comment_id: str,
    post_id: str,
    sender_id: str,
    sender_name: Optional[str],
    comment_text: str,
    is_edited: bool = False,
) -> None:
    """
    Background task to process a Facebook comment through the pipeline.
    Runs in a separate async task so the webhook returns 200 immediately.
    """
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            pipeline = CommentPipeline(session)
            await pipeline.process(
                comment_id=comment_id,
                post_id=post_id,
                sender_id=sender_id,
                sender_name=sender_name,
                comment_text=comment_text,
                is_edited=is_edited,
            )
            await session.commit()
    except Exception as e:
        # Print directly to stderr so Railway always captures it,
        # even if the structlog pipeline has issues.
        print(
            f"[CRITICAL] background_task_error comment_id={comment_id} error={e}",
            file=sys.stderr,
            flush=True,
        )
        logger.error(
            "background_task_error",
            comment_id=comment_id,
            error=str(e),
            exc_info=True,
        )


def schedule_comment_processing(
    comment_id: str,
    post_id: str,
    sender_id: str,
    sender_name: Optional[str],
    comment_text: str,
    is_edited: bool = False,
) -> None:
    """Schedule comment processing as a background asyncio task.

    The task reference is stored in ``_background_tasks`` so Python's garbage
    collector cannot discard it while it is still awaiting I/O (a known pitfall
    with asyncio.create_task in Python 3.11+).
    """
    task = asyncio.create_task(
        process_comment_task(
            comment_id=comment_id,
            post_id=post_id,
            sender_id=sender_id,
            sender_name=sender_name,
            comment_text=comment_text,
            is_edited=is_edited,
        )
    )
    # Keep a strong reference; remove it automatically once done.
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    logger.info("comment_scheduled", comment_id=comment_id, is_edited=is_edited)
