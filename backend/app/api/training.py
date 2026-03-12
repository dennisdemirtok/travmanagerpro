"""TravManager — Training API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db, get_current_stable
from app.models.game_state import GameState
from app.services import training_service

router = APIRouter()


class QuickTrainRequest(BaseModel):
    horse_id: UUID


class ProfessionalTrainRequest(BaseModel):
    horse_id: UUID
    target_stat: str
    trainer_level: str = "standard"


@router.post("/quick-train")
async def quick_train(
    req: QuickTrainRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Instant form training (costs 5,000 kr)."""
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    result = await training_service.quick_train(
        db, stable.id, req.horse_id, game_week
    )
    if "error" in result:
        return {"error": result["error"]}
    await db.commit()
    return result


@router.post("/professional")
async def send_to_professional(
    req: ProfessionalTrainRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Send horse to professional trainer (1-2 weeks)."""
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    result = await training_service.send_to_professional(
        db, stable.id, req.horse_id,
        req.target_stat, req.trainer_level, game_week,
    )
    if "error" in result:
        return {"error": result["error"]}
    await db.commit()
    return result


@router.get("/professional/status")
async def get_training_status(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Get active professional trainings."""
    return await training_service.get_active_trainings(db, stable.id)
