"""TravManager — Horse Observation (Diary) Model"""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class HorseObservation(Base):
    __tablename__ = "horse_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="CASCADE"), nullable=False)
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id", ondelete="CASCADE"), nullable=False)
    game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    observation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # equipment_positive, equipment_negative, condition_positive, condition_negative, mental_positive, mental_negative
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_level: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0.5)
    race_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("races.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
