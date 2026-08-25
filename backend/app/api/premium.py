"""TravManager — Premium, kosmetik och säsongspass API

OBS: köpändpunkterna tilldelar rättigheter utan betalning och är därför
avstängda när APP_ENV är production. Koppla in en betaltjänst först.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_db, get_current_stable
from app.models.game_state import GameState, Season
from app.services import premium_service

router = APIRouter()


class CosmeticRequest(BaseModel):
    item_key: str


async def _week(db: AsyncSession) -> int:
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()
    return gs.current_game_week if gs else 1


async def _season(db: AsyncSession):
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()
    if gs and gs.current_season_id:
        return await db.get(Season, gs.current_season_id)
    return None


def _require_dev():
    if settings.APP_ENV == "production" and not settings.DEBUG:
        raise HTTPException(
            status_code=501,
            detail="Köp är inte aktiverade. Betaltjänst måste kopplas in först.",
        )


@router.get("/status")
async def premium_status(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    return await premium_service.get_status(db, stable.id, await _week(db))


@router.post("/cosmetics/equip")
async def equip_cosmetic(
    req: CosmeticRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await premium_service.equip_cosmetic(db, stable.id, req.item_key, await _week(db))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.get("/season-pass")
async def season_pass(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    season = await _season(db)
    if season:
        await premium_service.sync_pass_points(db, stable.id, season)
        await db.commit()
    result = await premium_service.get_season_pass(
        db, stable.id, season.season_number if season else 1, await _week(db)
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/dev/grant-premium")
async def dev_grant_premium(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """DEV: aktivera premium utan betalning."""
    _require_dev()
    result = await premium_service.grant_premium(db, stable.id, await _week(db))
    await db.commit()
    return result


@router.post("/dev/grant-cosmetic")
async def dev_grant_cosmetic(
    req: CosmeticRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """DEV: lås upp kosmetik utan betalning."""
    _require_dev()
    result = await premium_service.grant_cosmetic(db, stable.id, req.item_key)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.post("/dev/grant-season-pass")
async def dev_grant_season_pass(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """DEV: aktivera säsongspass utan betalning."""
    _require_dev()
    season = await _season(db)
    result = await premium_service.grant_season_pass(
        db, stable.id, season.season_number if season else 1
    )
    await db.commit()
    return result
