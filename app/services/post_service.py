"""Service layer for post generation, scheduling, publishing, and moderation."""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import generate_post, generate_image_prompt
from app.config.settings import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.facebook.client import publish_post, get_post_insights
from app.models.post import PostStatus
from app.repositories.post_repository import PostRepository

logger = get_logger(__name__)


class PostService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PostRepository(session)

    # ── Generation ────────────────────────────────────────────────────────────

    async def generate_new_post(
        self,
        topic: Optional[str] = None,
        extra_instructions: Optional[str] = None,
        schedule_at: Optional[datetime] = None,
        auto_publish: bool = False,
        generate_image: bool = False,
    ):
        settings = get_settings()

        # 1. Generate post text
        content = await generate_post(topic=topic, extra_instructions=extra_instructions)

        # 2. Optionally generate image prompt
        image_url: Optional[str] = None
        image_prompt: Optional[str] = None

        if generate_image and settings.image_generation_enabled:
            try:
                image_prompt = await generate_image_prompt(content)
                image_url = await self._generate_image(image_prompt)
            except Exception as e:
                logger.warning("image_generation_failed", error=str(e))
                image_url = None

        # 3. Determine initial status
        if auto_publish or settings.post_auto_approve:
            if schedule_at:
                status = PostStatus.SCHEDULED
            else:
                status = PostStatus.APPROVED
        else:
            status = PostStatus.PENDING_APPROVAL

        # 4. Save to DB
        post = await self.repo.create(
            content=content,
            topic=topic,
            image_url=image_url,
            image_prompt=image_prompt,
            status=status,
            scheduled_at=schedule_at,
        )

        # 5. Publish immediately if approved and no schedule
        if status == PostStatus.APPROVED:
            post = await self._publish(post.id)

        logger.info("post_generated", post_id=post.id, status=post.status)
        return post

    # ── Approval / rejection ──────────────────────────────────────────────────

    async def approve_post(
        self,
        post_id: int,
        approved_by: str = "admin",
        publish_now: bool = False,
        schedule_at: Optional[datetime] = None,
    ):
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise AppException(404, "المنشور غير موجود")
        if post.status not in (PostStatus.PENDING_APPROVAL, PostStatus.DRAFT, PostStatus.REJECTED):
            raise AppException(400, f"لا يمكن اعتماد منشور بحالة: {post.status}")

        if publish_now:
            await self.repo.update_status(post_id, PostStatus.APPROVED, approved_by=approved_by)
            return await self._publish(post_id)
        elif schedule_at:
            return await self.repo.update_status(
                post_id,
                PostStatus.SCHEDULED,
                approved_by=approved_by,
                scheduled_at=schedule_at,
            )
        else:
            return await self.repo.update_status(
                post_id, PostStatus.APPROVED, approved_by=approved_by
            )

    async def reject_post(self, post_id: int, reason: Optional[str] = None):
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise AppException(404, "المنشور غير موجود")
        return await self.repo.update_status(
            post_id, PostStatus.REJECTED, rejection_reason=reason or ""
        )

    async def update_post_content(self, post_id: int, content: str, topic: Optional[str] = None):
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise AppException(404, "المنشور غير موجود")
        if post.status == PostStatus.PUBLISHED:
            raise AppException(400, "لا يمكن تعديل منشور تم نشره")
        return await self.repo.update_status(
            post_id,
            post.status,
            content=content,
            **({"topic": topic} if topic is not None else {}),
        )

    async def delete_post(self, post_id: int) -> bool:
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise AppException(404, "المنشور غير موجود")
        if post.status == PostStatus.PUBLISHING:
            raise AppException(400, "لا يمكن حذف منشور جاري نشره")
        return await self.repo.delete(post_id)

    # ── Publishing ────────────────────────────────────────────────────────────

    async def _publish(self, post_id: int):
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise AppException(404, "المنشور غير موجود")

        await self.repo.update_status(post_id, PostStatus.PUBLISHING)
        try:
            facebook_post_id = await publish_post(
                message=post.content,
                image_url=post.image_url,
            )
            now = datetime.now(timezone.utc)
            result = await self.repo.update_status(
                post_id,
                PostStatus.PUBLISHED,
                facebook_post_id=facebook_post_id,
                published_at=now,
            )
            logger.info("post_published", post_id=post_id, fb_post_id=facebook_post_id)
            return result
        except Exception as e:
            await self.repo.update_status(
                post_id, PostStatus.FAILED, error_message=str(e)
            )
            logger.error("post_publish_failed", post_id=post_id, error=str(e))
            raise

    async def publish_post_now(self, post_id: int):
        """Force publish a post (must be approved or scheduled)."""
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise AppException(404, "المنشور غير موجود")
        if post.status not in (PostStatus.APPROVED, PostStatus.SCHEDULED, PostStatus.FAILED):
            raise AppException(400, f"لا يمكن نشر منشور بحالة: {post.status}")
        return await self._publish(post_id)

    # ── Scheduler ─────────────────────────────────────────────────────────────

    async def process_due_posts(self):
        """Called by background scheduler — publish all due scheduled posts."""
        due = await self.repo.get_due_scheduled_posts()
        if not due:
            return
        logger.info("scheduler_processing_due_posts", count=len(due))
        for post in due:
            try:
                await self._publish(post.id)
            except Exception as e:
                logger.error("scheduler_post_failed", post_id=post.id, error=str(e))

    # ── Insights ──────────────────────────────────────────────────────────────

    async def refresh_insights(self, post_id: int):
        post = await self.repo.get_by_id(post_id)
        if not post or not post.facebook_post_id:
            return post
        insights = await get_post_insights(post.facebook_post_id)
        if insights:
            await self.repo.update_engagement(
                post_id,
                reactions=insights.get("reactions", 0),
                comments=insights.get("comments", 0),
                shares=insights.get("shares", 0),
                reach=insights.get("reach", 0),
            )
        return await self.repo.get_by_id(post_id)

    async def get_post_stats(self) -> dict:
        counts = await self.repo.count_by_status()
        all_posts = await self.repo.list_posts(limit=1000)
        return {
            "total": sum(counts.values()),
            "draft": counts.get("draft", 0),
            "pending_approval": counts.get("pending_approval", 0),
            "approved": counts.get("approved", 0),
            "scheduled": counts.get("scheduled", 0),
            "published": counts.get("published", 0),
            "failed": counts.get("failed", 0),
            "rejected": counts.get("rejected", 0),
            "total_reactions": sum(p.reactions_count for p in all_posts),
            "total_comments": sum(p.comments_count for p in all_posts),
            "total_shares": sum(p.shares_count for p in all_posts),
            "total_reach": sum(p.reach for p in all_posts),
        }

    # ── Image generation helper ───────────────────────────────────────────────

    async def _generate_image(self, prompt: str) -> Optional[str]:
        """Generate an image via DALL-E compatible API and return its URL."""
        from openai import AsyncOpenAI
        settings = get_settings()
        if not settings.image_generation_api_key:
            return None
        client = AsyncOpenAI(
            api_key=settings.image_generation_api_key,
            base_url=settings.image_generation_base_url,
        )
        try:
            response = await client.images.generate(
                model=settings.image_generation_model,
                prompt=prompt,
                n=1,
                size="1024x1024",
            )
            await client.close()
            return response.data[0].url if response.data else None
        except Exception as e:
            await client.close()
            logger.warning("dalle_error", error=str(e))
            return None
