"""TravManager — Finances API Routes"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.services import finance_service

router = APIRouter()


@router.get("/overview")
async def financial_overview(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    return await finance_service.get_financial_overview(db, stable.id)


@router.get("/transactions")
async def list_transactions(
    category: str = Query(default=None),
    game_week: int = Query(default=None),
    limit: int = Query(default=50),
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    txns = await finance_service.get_transactions(db, stable.id, category, game_week, limit)
    return {"transactions": txns, "total": len(txns)}
