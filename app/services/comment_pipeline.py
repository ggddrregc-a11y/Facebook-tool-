import json
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.emotion_detector import detect_emotion
from app.ai.provider import generate_reply
from app.ai.spam_detector import is_spam
from app.core.exceptions import (
    DuplicateCommentException,
    FacebookAPIException,
    SpamCommentException,
)
from app.core.logging import get_logger
from app.core.security import generate_comment_hash
from app.facebook.client import send_comment_reply
from app.repositories.comment_repository import CommentRepository
from app.repositories.log_repository import LogRepository
from app.repositories.statistic_repository import StatisticRepository

logger = get_logger(__name__)


class CommentPipeline:
    """
    Processes a Facebook comment through the full pipeline:
    Validation → Spam Detection → Duplicate Detection →
    Emotion Detection → AI Reply → Facebook Reply → Database
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.comment_repo = CommentRepository(session)
        self.log_repo = LogRepository(session)
        self.stat_repo = StatisticRepository(session)

    async def process(
        self,
        comment_id: str,
        post_id: str,
        sender_id: str,
        sender_name: Optional[str],
        comment_text: str,
        is_edited: bool = False,
    ) -> None:
        """Main pipeline entry point."""
        logger.info(
            "pipeline_start",
            comment_id=comment_id,
            sender_id=sender_id,
            is_edited=is_edited,
        )

        # Step 1: Check if already processed
        existing = await self.comment_repo.get_by_comment_id(comment_id)
        if existing and not is_edited:
            logger.info("pipeline_already_processed", comment_id=comment_id)
            return

        # Step 2: Validate and spam check
        spam_result, spam_reason = is_spam(comment_text)
        comment_hash = generate_comment_hash(comment_text)

        # Step 3: Create or update comment record
        if existing and is_edited:
            # Re-process edited comment
            comment = existing
        else:
            comment = await self.comment_repo.create_comment(
                comment_id=comment_id,
                post_id=post_id,
                sender_id=sender_id,
                sender_name=sender_name,
                comment_text=comment_text,
                comment_hash=comment_hash,
                is_edited=is_edited,
            )

        # Step 4: Handle spam
        if spam_result:
            await self.comment_repo.mark_as_spam(comment_id)
            await self.log_repo.create_log(
                level="INFO",
                event="comment_spam_detected",
                message=spam_reason,
                source="pipeline",
                comment_id=comment_id,
            )
            logger.info("pipeline_spam", comment_id=comment_id, reason=spam_reason)
            return

        # Step 5: Detect emotion
        emotion = detect_emotion(comment_text)

        # Step 6: Duplicate detection - reuse reply if available
        duplicate_comment = await self.comment_repo.get_by_hash(comment_hash)
        if duplicate_comment and duplicate_comment.comment_id != comment_id:
            reused_reply = duplicate_comment.ai_reply
            if reused_reply:
                # Try sending reused reply
                try:
                    await send_comment_reply(comment_id, reused_reply)
                    await self.comment_repo.update_reply(
                        comment_id=comment_id,
                        emotion=emotion,
                        ai_reply=reused_reply,
                        reply_sent=True,
                        reply_failed=False,
                        is_duplicate=True,
                        reused_reply=True,
                    )
                    await self._update_stats(emotion)
                    logger.info(
                        "pipeline_duplicate_reply_reused",
                        comment_id=comment_id,
                        original_id=duplicate_comment.comment_id,
                    )
                except FacebookAPIException as e:
                    await self.comment_repo.update_reply(
                        comment_id=comment_id,
                        emotion=emotion,
                        ai_reply=reused_reply,
                        reply_sent=False,
                        reply_failed=True,
                        is_duplicate=True,
                        reused_reply=True,
                        error_message=str(e),
                    )
                    await self._log_error(comment_id, "facebook_reply_failed", str(e))
                return

        # Step 7: Generate AI reply
        try:
            ai_reply = await generate_reply(comment_text, emotion)
        except Exception as e:
            await self.comment_repo.update_reply(
                comment_id=comment_id,
                emotion=emotion,
                ai_reply=None,
                reply_sent=False,
                reply_failed=True,
                error_message=str(e),
            )
            await self._log_error(comment_id, "ai_reply_failed", str(e))
            logger.error("pipeline_ai_error", comment_id=comment_id, error=str(e))
            return

        # Step 8: Send reply to Facebook
        try:
            await send_comment_reply(comment_id, ai_reply)
            await self.comment_repo.update_reply(
                comment_id=comment_id,
                emotion=emotion,
                ai_reply=ai_reply,
                reply_sent=True,
                reply_failed=False,
            )
            await self._update_stats(emotion)
            logger.info(
                "pipeline_complete",
                comment_id=comment_id,
                emotion=emotion,
                reply_length=len(ai_reply),
            )
        except FacebookAPIException as e:
            await self.comment_repo.update_reply(
                comment_id=comment_id,
                emotion=emotion,
                ai_reply=ai_reply,
                reply_sent=False,
                reply_failed=True,
                error_message=str(e),
            )
            await self._log_error(comment_id, "facebook_reply_failed", str(e))
            logger.error("pipeline_facebook_error", comment_id=comment_id, error=str(e))

    async def _update_stats(self, emotion: str) -> None:
        try:
            await self.stat_repo.increment_emotion(emotion, date.today())
        except Exception as e:
            logger.warning("stats_update_failed", error=str(e))

    async def _log_error(self, comment_id: str, event: str, message: str) -> None:
        try:
            await self.log_repo.create_log(
                level="ERROR",
                event=event,
                message=message,
                source="pipeline",
                comment_id=comment_id,
            )
        except Exception as e:
            logger.warning("log_write_failed", error=str(e))
