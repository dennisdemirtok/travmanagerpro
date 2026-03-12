"""TravManager — Drivers API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.services import driver_service
from app.api.schemas import DriverContractRequest

router = APIRouter()


@router.get("")
async def list_drivers(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    return await driver_service.list_drivers(db, stable.id)


@router.get("/{driver_id}/compatibility/{horse_id}")
async def get_compatibility(
    driver_id: UUID,
    horse_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await driver_service.get_compatibility(db, driver_id, horse_id, stable.id)
    if not result:
        raise HTTPException(status_code=404, detail="Kusk eller hast hittades inte")
    return result


@router.post("/{driver_id}/compatibility/{horse_id}/check")
async def check_compatibility_paid(
    driver_id: UUID,
    horse_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Paid compatibility check. Deducts 50,000 ore."""
    result = await driver_service.check_compatibility_paid(db, driver_id, horse_id, stable.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{driver_id}/contract")
async def manage_contract(
    driver_id: UUID,
    req: DriverContractRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await driver_service.renew_contract(db, driver_id, stable.id, req.contract_type, req.weeks)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/{driver_id}/contract")
async def terminate_contract(
    driver_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await driver_service.terminate_contract(db, driver_id, stable.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
