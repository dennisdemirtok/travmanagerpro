"""TravManager — Sponsor API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.services import sponsor_service
from app.services.game_init_service import calculate_game_time
from app.models.game_state import GameState
from sqlalchemy import select

router = APIRouter()


class SignSponsorRequest(BaseModel):
    sponsor_id: UUID


@router.get("")
async def list_sponsors(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """List all sponsors with eligibility and contract status."""
    sponsors = await sponsor_service.get_available_sponsors(db, stable.id)
    return {"sponsors": sponsors}


@router.get("/contracts")
async def my_contracts(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Get active sponsor contracts."""
    contracts = await sponsor_service.get_active_contracts(db, stable.id)
    return {"contracts": contracts}


@router.post("/sign")
async def sign_sponsor(
    req: SignSponsorRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Sign a sponsor contract."""
    gs = await db.execute(select(GameState).where(GameState.id == 1))
    game_state = gs.scalar_one_or_none()
    game_week = 1
    if game_state:
        gt = calculate_game_time(game_state.real_week_start)
        game_week = gt["game_week"]

    result = await sponsor_service.sign_sponsor_contract(
        db, stable.id, req.sponsor_id, game_week
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/contracts/{contract_id}")
async def terminate_contract(
    contract_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a sponsor contract."""
    result = await sponsor_service.terminate_sponsor_contract(db, stable.id, contract_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/collect")
async def collect_sponsor_income(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Manually collect weekly sponsor income. Only available on Saturdays."""
    gs = await db.execute(select(GameState).where(GameState.id == 1))
    game_state = gs.scalar_one_or_none()
    if not game_state:
        raise HTTPException(status_code=500, detail="Spelstatus saknas")

    gt = calculate_game_time(game_state.real_week_start)
    game_week = gt["game_week"]
    game_day = gt["game_day"]

    result = await sponsor_service.collect_player_sponsor_income(
        db, stable.id, game_week, game_day
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    await db.commit()
    return result
