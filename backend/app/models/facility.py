"""TravManager — Facility, Staff, FeedPlan Models"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base, PgEnum
from app.models.enums import FacilityType, FeedType, StaffRole


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id", ondelete="CASCADE"), nullable=False)
    facility_type: Mapped[FacilityType] = mapped_column(PgEnum(FacilityType, "facility_type"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    build_cost: Mapped[int] = mapped_column(BigInteger, nullable=False)
    maintenance_cost_per_week: Mapped[int] = mapped_column(BigInteger, default=0)
    built_at: Mapped[datetime] = mapped_column(server_default=func.now())

    stable = relationship("Stable", back_populates="facilities")


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[StaffRole] = mapped_column(PgEnum(StaffRole, "staff_role"), nullable=False)
    quality: Mapped[int] = mapped_column(Integer, default=50)
    salary_per_week: Mapped[int] = mapped_column(BigInteger, nullable=False)
    contract_ends_week: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class FeedPlan(Base):
    __tablename__ = "feed_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="CASCADE"), nullable=False)
    feed_type: Mapped[FeedType] = mapped_column(PgEnum(FeedType, "feed_type"), nullable=False)
    percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_per_week: Mapped[int] = mapped_column(BigInteger, nullable=False)

    horse = relationship("Horse", back_populates="feed_plans")
