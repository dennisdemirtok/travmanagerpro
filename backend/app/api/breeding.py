"""TravManager — Breeding API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.models.game_state import GameState
from app.services import breeding_service
from sqlalchemy import select

router = APIRouter()


class BreedRequest(BaseModel):
    mare_id: UUID
    stallion_id: UUID


@router.get("/stallions")
async def get_stallions(db: AsyncSession = Depends(get_db)):
    """Get all available stallions for breeding."""
    return await breeding_service.get_available_stallions(db)


@router.post("/breed")
async def breed(
    req: BreedRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Start breeding: mare + stallion."""
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    result = await breeding_service.breed_horse(
        db, stable.id, req.mare_id, req.stallion_id, game_week
    )
    if "error" in result:
        return {"error": result["error"]}
    await db.commit()
    return result


@router.get("/status")
async def breeding_status(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Get breeding/pregnancy status for mares."""
    return await breeding_service.get_breeding_status(db, stable.id)


@router.get("/pedigree/{horse_id}")
async def get_pedigree(
    horse_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get 3-generation pedigree for a horse."""
    pedigree = await breeding_service.get_horse_pedigree(db, horse_id)
    if not pedigree:
        return {"error": "Ingen stamtavla hittad"}
    return pedigree
