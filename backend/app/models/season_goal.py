"""TravManager — Säsongsmål (sprint 6)"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class SeasonGoal(Base):
    __tablename__ = "season_goals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stables.id", ondelete="CASCADE"), nullable=False)
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    goal_key: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    target: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    progress: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    reward_money: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    reward_reputation: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    reward_text: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    completed_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
