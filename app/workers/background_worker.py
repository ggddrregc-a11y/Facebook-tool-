import asyncio
from typing import Optional

from app.core.logging import get_logger
from app.database.session import get_session_factory
from app.services.comment_pipeline import CommentPipeline

logger = get_logger(__name__)


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
    """Schedule comment processing as a background asyncio task."""
    asyncio.create_task(
        process_comment_task(
            comment_id=comment_id,
            post_id=post_id,
            sender_id=sender_id,
            sender_name=sender_name,
            comment_text=comment_text,
            is_edited=is_edited,
        )
    )
    logger.info("comment_scheduled", comment_id=comment_id, is_edited=is_edited)
