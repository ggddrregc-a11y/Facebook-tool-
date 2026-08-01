from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.repositories.base import BaseRepository


class LogRepository(BaseRepository[Log]):
    def __init__(self, session: AsyncSession):
        super().__init__(Log, session)

    async def create_log(
        self,
        level: str,
        event: str,
        message: Optional[str] = None,
        source: Optional[str] = None,
        comment_id: Optional[str] = None,
        extra_data: Optional[str] = None,
    ) -> Log:
        return await self.create(
            level=level,
            event=event,
            message=message,
            source=source,
            comment_id=comment_id,
            extra_data=extra_data,
        )

    async def get_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        level: Optional[str] = None,
    ) -> tuple[int, list[Log]]:
        query = select(Log)
        count_query = select(func.count()).select_from(Log)

        if level:
            query = query.where(Log.level == level)
            count_query = count_query.where(Log.level == level)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        offset = (page - 1) * per_page
        query = query.order_by(Log.created_at.desc()).offset(offset).limit(per_page)
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return total, items
