from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.statistic import Statistic
from app.repositories.base import BaseRepository


class StatisticRepository(BaseRepository[Statistic]):
    def __init__(self, session: AsyncSession):
        super().__init__(Statistic, session)

    async def increment_emotion(self, emotion: str, stat_date: date) -> None:
        stmt = (
            insert(Statistic)
            .values(stat_date=stat_date, emotion=emotion, count=1)
            .on_conflict_do_update(
                index_elements=["stat_date", "emotion"],
                set_={"count": Statistic.count + 1},
            )
        )
        await self.session.execute(stmt)

    async def get_emotion_totals(self) -> list[dict]:
        from sqlalchemy import func
        result = await self.session.execute(
            select(
                Statistic.emotion,
                func.sum(Statistic.count).label("total"),
            ).group_by(Statistic.emotion)
        )
        return [{"emotion": row.emotion, "count": int(row.total)} for row in result]

    async def get_last_7_days(self) -> list[Statistic]:
        from sqlalchemy import func
        from datetime import timedelta
        cutoff = date.today() - timedelta(days=7)
        result = await self.session.execute(
            select(Statistic)
            .where(Statistic.stat_date >= cutoff)
            .order_by(Statistic.stat_date)
        )
        return list(result.scalars().all())
