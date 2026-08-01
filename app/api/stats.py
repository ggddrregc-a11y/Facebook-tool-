from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.middlewares.auth_middleware import require_admin
from app.schemas.stats import DashboardStats
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api", tags=["Statistics"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
) -> DashboardStats:
    service = StatsService(db)
    return await service.get_dashboard_stats()
