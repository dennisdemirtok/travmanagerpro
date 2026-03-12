"""TravManager — Event Service"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import StableEvent


async def create_event(
    db: AsyncSession, stable_id, event_type: str, title: str,
    description: str, game_week: int, requires_action: bool = False,
    action_data: dict = None,
):
    event = StableEvent(
        stable_id=stable_id, event_type=event_type, title=title,
        description=description, game_week=game_week,
        requires_action=requires_action, action_data=action_data,
    )
    db.add(event)
    await db.flush()
    return event


async def get_events(db: AsyncSession, stable_id, unread_only=False, limit=20):
    q = select(StableEvent).where(StableEvent.stable_id == stable_id)
    if unread_only:
        q = q.where(StableEvent.is_read == False)
    q = q.order_by(StableEvent.created_at.desc()).limit(limit)
    result = await db.execute(q)
    events = result.scalars().all()
    return [
        {
            "id": str(e.id), "event_type": e.event_type.value if hasattr(e.event_type, 'value') else e.event_type,
            "title": e.title, "description": e.description,
            "is_read": e.is_read, "requires_action": e.requires_action,
            "action_data": e.action_data, "game_week": e.game_week,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


async def handle_action(db: AsyncSession, event_id, stable_id):
    """Handle an event that requires action (mark as read/handled)."""
    result = await db.execute(
        select(StableEvent).where(StableEvent.id == event_id, StableEvent.stable_id == stable_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        return {"error": "Handelse hittades inte"}

    event.is_read = True
    event.requires_action = False
    await db.flush()
    return {"success": True, "event_id": str(event.id)}


async def mark_read(db: AsyncSession, event_id, stable_id):
    """Mark an event as read."""
    result = await db.execute(
        select(StableEvent).where(StableEvent.id == event_id, StableEvent.stable_id == stable_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        return {"error": "Handelse hittades inte"}

    event.is_read = True
    await db.flush()
    return {"success": True}
