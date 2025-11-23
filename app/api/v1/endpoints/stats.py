from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.stats import StatsResponse
from app.services.stats_service import StatsService

router = APIRouter()


@router.get("/", summary="Получить статистику по сервису", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await StatsService.get_stats(db)
