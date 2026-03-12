"""TravManager — Stable Model"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Stable(Base):
    __tablename__ = "stables"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    reputation: Mapped[int] = mapped_column(Integer, default=10, server_default="10")
    fan_count: Mapped[int] = mapped_column(Integer, default=100, server_default="100")
    balance: Mapped[int] = mapped_column(BigInteger, default=200000, server_default="200000")
    total_earnings: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    division_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("divisions.id"), nullable=True)
    division_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season_points: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    home_track_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("race_tracks.id"), nullable=True)
    max_horses: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    box_upgrade_level: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_npc: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    npc_difficulty: Mapped[int] = mapped_column(Integer, default=50, server_default="50")
    last_press_release_week: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_sponsor_collection_week: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    user = relationship("User", back_populates="stable")
    horses = relationship("Horse", back_populates="stable")
    driver_contracts = relationship("DriverContract", back_populates="stable")
    facilities = relationship("Facility", back_populates="stable")
    transactions = relationship("Transaction", back_populates="stable")
    events = relationship("StableEvent", back_populates="stable")
