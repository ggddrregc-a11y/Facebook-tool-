from datetime import datetime, timezone, date
from typing import Optional

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.repositories.base import BaseRepository
from app.schemas.comment import CommentSearchParams


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Comment, session)

    async def get_by_comment_id(self, comment_id: str) -> Optional[Comment]:
        result = await self.session.execute(
            select(Comment).where(Comment.comment_id == comment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, comment_hash: str) -> Optional[Comment]:
        result = await self.session.execute(
            select(Comment)
            .where(
                and_(
                    Comment.comment_hash == comment_hash,
                    Comment.reply_sent == True,
                    Comment.ai_reply.is_not(None),
                )
            )
            .order_by(Comment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_comment(
        self,
        comment_id: str,
        post_id: str,
        sender_id: str,
        sender_name: Optional[str],
        comment_text: str,
        comment_hash: str,
        is_edited: bool = False,
    ) -> Comment:
        return await self.create(
            comment_id=comment_id,
            post_id=post_id,
            sender_id=sender_id,
            sender_name=sender_name,
            comment_text=comment_text,
            comment_hash=comment_hash,
            is_edited=is_edited,
        )

    async def update_reply(
        self,
        comment_id: str,
        emotion: str,
        ai_reply: str,
        reply_sent: bool,
        reply_failed: bool,
        is_spam: bool = False,
        is_duplicate: bool = False,
        reused_reply: bool = False,
        error_message: Optional[str] = None,
    ) -> None:
        await self.session.execute(
            update(Comment)
            .where(Comment.comment_id == comment_id)
            .values(
                emotion=emotion,
                ai_reply=ai_reply,
                reply_sent=reply_sent,
                reply_failed=reply_failed,
                is_spam=is_spam,
                is_duplicate=is_duplicate,
                reused_reply=reused_reply,
                error_message=error_message,
                processed_at=datetime.now(timezone.utc),
            )
        )

    async def mark_as_spam(self, comment_id: str) -> None:
        await self.session.execute(
            update(Comment)
            .where(Comment.comment_id == comment_id)
            .values(
                is_spam=True,
                processed_at=datetime.now(timezone.utc),
            )
        )

    async def search(self, params: CommentSearchParams) -> tuple[int, list[Comment]]:
        query = select(Comment)
        count_query = select(func.count()).select_from(Comment)

        filters = []
        if params.q:
            filters.append(
                or_(
                    Comment.comment_text.ilike(f"%{params.q}%"),
                    Comment.sender_name.ilike(f"%{params.q}%"),
                    Comment.ai_reply.ilike(f"%{params.q}%"),
                )
            )
        if params.emotion:
            filters.append(Comment.emotion == params.emotion)
        if params.reply_sent is not None:
            filters.append(Comment.reply_sent == params.reply_sent)
        if params.is_spam is not None:
            filters.append(Comment.is_spam == params.is_spam)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        offset = (params.page - 1) * params.per_page
        query = (
            query.order_by(Comment.created_at.desc())
            .offset(offset)
            .limit(params.per_page)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return total, items

    async def get_today_count(self) -> int:
        today = date.today()
        result = await self.session.execute(
            select(func.count()).select_from(Comment).where(
                func.date(Comment.created_at) == today
            )
        )
        return result.scalar_one()

    async def get_failed_count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Comment).where(
                Comment.reply_failed == True
            )
        )
        return result.scalar_one()

    async def get_replied_count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Comment).where(
                Comment.reply_sent == True
            )
        )
        return result.scalar_one()

    async def get_spam_count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Comment).where(
                Comment.is_spam == True
            )
        )
        return result.scalar_one()

    async def get_duplicate_count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Comment).where(
                Comment.is_duplicate == True
            )
        )
        return result.scalar_one()

    async def get_emotion_stats(self) -> list[dict]:
        result = await self.session.execute(
            select(Comment.emotion, func.count(Comment.id).label("count"))
            .where(Comment.emotion.is_not(None))
            .group_by(Comment.emotion)
            .order_by(func.count(Comment.id).desc())
        )
        return [{"emotion": row.emotion, "count": row.count} for row in result]

    async def get_recent(self, limit: int = 10) -> list[Comment]:
        result = await self.session.execute(
            select(Comment)
            .order_by(Comment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
