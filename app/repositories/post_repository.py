"""Repository for ScheduledPost CRUD operations."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, func, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import ScheduledPost, PostStatus


class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> ScheduledPost:
        post = ScheduledPost(**kwargs)
        self.session.add(post)
        await self.session.flush()
        return post

    async def get_by_id(self, post_id: int) -> Optional[ScheduledPost]:
        result = await self.session.execute(
            select(ScheduledPost).where(ScheduledPost.id == post_id)
        )
        return result.scalar_one_or_none()

    async def list_posts(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ScheduledPost]:
        q = select(ScheduledPost).order_by(desc(ScheduledPost.created_at))
        if status:
            q = q.where(ScheduledPost.status == status)
        q = q.limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def count(self, status: Optional[str] = None) -> int:
        q = select(func.count()).select_from(ScheduledPost)
        if status:
            q = q.where(ScheduledPost.status == status)
        result = await self.session.execute(q)
        return result.scalar_one()

    async def update_status(
        self,
        post_id: int,
        status: str,
        **extra_fields,
    ) -> Optional[ScheduledPost]:
        values = {"status": status, **extra_fields}
        await self.session.execute(
            update(ScheduledPost)
            .where(ScheduledPost.id == post_id)
            .values(**values)
        )
        await self.session.flush()
        return await self.get_by_id(post_id)

    async def get_due_scheduled_posts(self) -> List[ScheduledPost]:
        """Return posts that are scheduled and past their scheduled_at time."""
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(ScheduledPost)
            .where(ScheduledPost.status == PostStatus.SCHEDULED)
            .where(ScheduledPost.scheduled_at <= now)
            .order_by(ScheduledPost.scheduled_at)
        )
        return list(result.scalars().all())

    async def delete(self, post_id: int) -> bool:
        post = await self.get_by_id(post_id)
        if post:
            await self.session.delete(post)
            await self.session.flush()
            return True
        return False

    async def update_engagement(
        self,
        post_id: int,
        reactions: int = 0,
        comments: int = 0,
        shares: int = 0,
        reach: int = 0,
    ) -> None:
        await self.session.execute(
            update(ScheduledPost)
            .where(ScheduledPost.id == post_id)
            .values(
                reactions_count=reactions,
                comments_count=comments,
                shares_count=shares,
                reach=reach,
            )
        )
        await self.session.flush()

    async def count_by_status(self) -> dict:
        result = await self.session.execute(
            select(ScheduledPost.status, func.count().label("cnt"))
            .group_by(ScheduledPost.status)
        )
        return {row.status: row.cnt for row in result}
