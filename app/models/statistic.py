from datetime import date
from sqlalchemy import Date, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Statistic(Base, TimestampMixin):
    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    emotion: Mapped[str] = mapped_column(String(50), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("ix_statistics_date_emotion", "stat_date", "emotion", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Statistic date={self.stat_date} emotion={self.emotion} count={self.count}>"
