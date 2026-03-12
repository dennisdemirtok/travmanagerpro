"""TravManager — Horse Market / Auction API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db, get_current_stable
from app.services import market_service
from app.services.game_init_service import calculate_game_time
from app.models.game_state import GameState

router = APIRouter()


class ListHorseRequest(BaseModel):
    horse_id: UUID
    starting_price: int
    buyout_price: Optional[int] = None


class PlaceBidRequest(BaseModel):
    amount: int


async def _get_game_week(db: AsyncSession) -> int:
    gs = await db.execute(select(GameState).where(GameState.id == 1))
    game_state = gs.scalar_one_or_none()
    if game_state:
        gt = calculate_game_time(game_state.real_week_start)
        return gt["game_week"]
    return 1


@router.get("/listings")
async def get_listings(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Get all active market listings."""
    game_week = await _get_game_week(db)
    listings = await market_service.get_market_listings(db, stable.id, game_week)
    return {"listings": listings, "current_game_week": game_week}


@router.post("/list")
async def list_horse(
    req: ListHorseRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """List a horse for sale."""
    game_week = await _get_game_week(db)
    result = await market_service.list_horse_for_sale(
        db, stable.id, req.horse_id,
        req.starting_price, req.buyout_price,
        game_week,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/listings/{listing_id}/bid")
async def bid_on_listing(
    listing_id: UUID,
    req: PlaceBidRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Place a bid on a horse listing."""
    game_week = await _get_game_week(db)
    result = await market_service.place_bid(
        db, stable.id, listing_id, req.amount, game_week,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/listings/{listing_id}/buyout")
async def buyout_listing(
    listing_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Buy a horse at the buyout price."""
    game_week = await _get_game_week(db)
    result = await market_service.buyout_horse(
        db, stable.id, listing_id, game_week,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/listings/{listing_id}/accept")
async def accept_bid(
    listing_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Accept the current highest bid on a listing (early sale)."""
    game_week = await _get_game_week(db)
    result = await market_service.accept_bid(db, stable.id, listing_id, game_week)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/give-away/{horse_id}")
async def give_away_horse(
    horse_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Give away a horse (release from stable)."""
    result = await market_service.give_away_horse(db, stable.id, horse_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/listings/{listing_id}")
async def cancel_listing(
    listing_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an active listing (only if no bids)."""
    result = await market_service.cancel_listing(db, stable.id, listing_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/horse/{horse_id}")
async def get_horse_profile(
    horse_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get public profile of any horse (stats + race history)."""
    profile = await market_service.get_horse_public_profile(db, horse_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Hästen hittades inte")
    return profile
