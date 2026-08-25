"""TravManager — Balansverktyg (dev). Göms i produktion."""
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.services import balance_service

router = APIRouter()


@router.get("/simulate")
async def balance_simulation(
    runs: int = Query(default=100, ge=1, le=500),
    field_size: int = Query(default=12, ge=6, le=12),
    distance: int = Query(default=2140, ge=1000, le=3200),
    stretch_class: str = Query(default="medium"),
    seed: int = Query(default=20260101),
):
    """Kör N lopp med ett jämnt fält och mät taktikbalansen.

    Mål: ingen position/tempo-kombination ska vinna över 30 %.
    """
    if settings.APP_ENV == "production" and not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    if stretch_class not in ("short", "medium", "long"):
        raise HTTPException(status_code=400, detail="stretch_class måste vara short, medium eller long")

    return balance_service.run_balance_test(
        runs=runs, field_size=field_size, distance=distance,
        stretch_class=stretch_class, seed=seed,
    )
