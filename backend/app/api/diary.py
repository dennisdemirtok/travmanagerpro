"""TravManager — Hästdagbok och motståndsanalys API"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.models.game_state import GameState
from app.services import diary_service

router = APIRouter()


class NoteRequest(BaseModel):
    text: str


class TagRequest(BaseModel):
    tag: str


async def _week(db: AsyncSession) -> int:
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()
    return gs.current_game_week if gs else 1


@router.get("/horse/{horse_id}")
async def get_diary(
    horse_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await diary_service.get_diary(db, stable.id, horse_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/horse/{horse_id}/notes")
async def add_note(
    horse_id: UUID,
    req: NoteRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await diary_service.add_note(db, stable.id, horse_id, req.text, await _week(db))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await diary_service.delete_note(db, stable.id, note_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    await db.commit()
    return result


@router.post("/horse/{horse_id}/tags")
async def add_tag(
    horse_id: UUID,
    req: TagRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await diary_service.add_tag(db, stable.id, horse_id, req.tag)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await diary_service.delete_tag(db, stable.id, tag_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    await db.commit()
    return result


@router.get("/analysis/{race_id}/{horse_id}")
async def opposition_analysis(
    race_id: UUID,
    horse_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Motståndsanalys inför anmälan — din häst mot det förväntade fältet."""
    result = await diary_service.analyze_opposition(db, race_id, horse_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
