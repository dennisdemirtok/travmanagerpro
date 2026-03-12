"""TravManager — Breeding Models

Stallion registry, horse pedigree, and professional training.
"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class StallionRegistry(Base):
    __tablename__ = "stallion_registry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    origin_country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    stud_fee: Mapped[int] = mapped_column(BigInteger, nullable=False)
    speed_bonus: Mapped[int] = mapped_column(Integer, default=0)
    endurance_bonus: Mapped[int] = mapped_column(Integer, default=0)
    mentality_bonus: Mapped[int] = mapped_column(Integer, default=0)
    sprint_bonus: Mapped[int] = mapped_column(Integer, default=0)
    balance_bonus: Mapped[int] = mapped_column(Integer, default=0)
    strength_bonus: Mapped[int] = mapped_column(Integer, default=0)
    start_bonus: Mapped[int] = mapped_column(Integer, default=0)
    prestige: Mapped[int] = mapped_column(Integer, default=50)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class HorsePedigree(Base):
    __tablename__ = "horse_pedigree"

    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="CASCADE"), primary_key=True)
    sire_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sire_origin: Mapped[str | None] = mapped_column(String(10), nullable=True)
    dam_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dam_origin: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sire_sire_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sire_dam_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dam_sire_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dam_dam_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ProfessionalTraining(Base):
    __tablename__ = "professional_training"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="CASCADE"), nullable=False)
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=False)
    target_stat: Mapped[str] = mapped_column(String(30), nullable=False)
    trainer_level: Mapped[str] = mapped_column(String(20), default="standard")
    cost_per_week: Mapped[int] = mapped_column(BigInteger, nullable=False)
    start_week: Mapped[int] = mapped_column(Integer, nullable=False)
    end_week: Mapped[int] = mapped_column(Integer, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    stat_gain: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
