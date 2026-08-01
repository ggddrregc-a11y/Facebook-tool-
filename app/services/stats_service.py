from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.comment_repository import CommentRepository
from app.repositories.log_repository import LogRepository
from app.repositories.statistic_repository import StatisticRepository
from app.schemas.stats import DashboardStats, EmotionStat

logger = get_logger(__name__)

EMOTION_LABEL_MAP = {
    "دعاء": "دعاء",
    "حزن": "حزن",
    "فرح": "فرح",
    "حب": "حب",
    "إعجاب": "إعجاب",
    "سؤال": "سؤال",
    "غضب": "غضب",
    "إيموجي": "إيموجي",
    "محايد": "محايد",
}


class StatsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.comment_repo = CommentRepository(session)
        self.stat_repo = StatisticRepository(session)
        self.log_repo = LogRepository(session)

    async def get_dashboard_stats(self) -> DashboardStats:
        total_comments = await self.comment_repo.count()
        total_replies = await self.comment_repo.get_replied_count()
        failed_replies = await self.comment_repo.get_failed_count()
        today_comments = await self.comment_repo.get_today_count()
        spam_comments = await self.comment_repo.get_spam_count()
        duplicate_comments = await self.comment_repo.get_duplicate_count()
        emotion_data = await self.comment_repo.get_emotion_stats()

        emotion_stats = [
            EmotionStat(
                emotion=item["emotion"],
                count=item["count"],
                label=EMOTION_LABEL_MAP.get(item["emotion"], item["emotion"]),
            )
            for item in emotion_data
        ]

        return DashboardStats(
            total_comments=total_comments,
            total_replies=total_replies,
            failed_replies=failed_replies,
            today_comments=today_comments,
            spam_comments=spam_comments,
            duplicate_comments=duplicate_comments,
            emotion_stats=emotion_stats,
        )
