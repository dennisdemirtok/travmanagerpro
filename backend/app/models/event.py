"""TravManager — Event Models"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base, PgEnum
from app.models.enums import EventType, PressTone


class StableEvent(Base):
    __tablename__ = "stable_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=False)
    event_type: Mapped[EventType] = mapped_column(PgEnum(EventType, "event_type"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_action: Mapped[bool] = mapped_column(Boolean, default=False)
    action_data = mapped_column(JSONB, nullable=True)
    game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)

    stable = relationship("Stable", back_populates="events")


class PressRelease(Base):
    __tablename__ = "press_releases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=False)
    tone: Mapped[PressTone] = mapped_column(PgEnum(PressTone, "press_tone"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    pr_points: Mapped[int] = mapped_column(Integer, default=0)
    income_generated: Mapped[int] = mapped_column(BigInteger, default=0)
    game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
