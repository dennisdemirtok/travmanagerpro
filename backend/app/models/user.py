"""TravManager — User Model"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    login_streak: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_supporter: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    supporter_tier: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    supporter_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_npc: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    locale: Mapped[str] = mapped_column(String(10), default="sv", server_default="sv")
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Stockholm", server_default="Europe/Stockholm")

    stable = relationship("Stable", back_populates="user", uselist=False)
