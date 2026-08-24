"""TravManager — Finances API Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.models.game_state import GameState
from app.services import finance_service

router = APIRouter()


class LoanRequest(BaseModel):
    amount: int  # öre


class RestartRequest(BaseModel):
    keep_horse_id: str | None = None


async def _current_week(db: AsyncSession) -> int:
    result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = result.scalar_one_or_none()
    return gs.current_game_week if gs else 1


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


@router.get("/debt")
async def debt_status(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    return await finance_service.get_debt_status(db, stable.id)


@router.post("/loan")
async def take_loan(
    body: LoanRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    week = await _current_week(db)
    result = await finance_service.take_loan(db, stable.id, body.amount, week)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.post("/loan/repay")
async def repay_loan(
    body: LoanRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    week = await _current_week(db)
    result = await finance_service.repay_loan(db, stable.id, body.amount, week)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.post("/restart")
async def restart_stable(
    body: RestartRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    week = await _current_week(db)
    result = await finance_service.restart_stable(db, stable.id, week, body.keep_horse_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result
