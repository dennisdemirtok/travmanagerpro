"""TravManager — Caretaker (Skötare) API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import CaretakerHireRequest
from app.core.deps import get_db, get_current_stable
from app.services import caretaker_service

router = APIRouter()


@router.get("")
async def list_caretakers(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Get available caretakers and current stable assignments."""
    available = await caretaker_service.get_available_caretakers(db)
    assignments = await caretaker_service.get_stable_assignments(db, stable.id)
    reports = await caretaker_service.get_scout_reports_for_stable(db, stable.id)
    return {
        "available": available,
        "assignments": assignments,
        "scout_reports": reports,
    }


@router.post("/{caretaker_id}/scout/{horse_id}")
async def scout_caretaker(
    caretaker_id: UUID,
    horse_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Scout a caretaker to reveal compatibility with a specific horse. Costs 750 kr."""
    result = await caretaker_service.scout_caretaker(db, caretaker_id, horse_id, stable.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{caretaker_id}/hire")
async def hire_caretaker(
    caretaker_id: UUID,
    req: CaretakerHireRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Make a salary offer to hire a caretaker for a horse."""
    result = await caretaker_service.hire_caretaker(
        db, caretaker_id, req.horse_id, stable.id, req.offered_salary,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/assignment/{assignment_id}")
async def fire_caretaker(
    assignment_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Fire a caretaker (release from horse)."""
    result = await caretaker_service.fire_caretaker(db, assignment_id, stable.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/horse/{horse_id}")
async def horse_caretaker(
    horse_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Get caretaker info for a specific horse."""
    info = await caretaker_service.get_horse_caretaker(db, horse_id)
    return info or {"message": "Ingen skötare tilldelad"}
