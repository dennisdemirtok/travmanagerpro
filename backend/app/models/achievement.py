"""TravManager — Achievement Models"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class AchievementDefinition(Base):
    __tablename__ = "achievement_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=10)
    reward_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(10), default="*")


class StableAchievement(Base):
    __tablename__ = "stable_achievements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=False)
    achievement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("achievement_definitions.id"), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(server_default=func.now())
    game_week: Mapped[int] = mapped_column(Integer, nullable=False)
