"""TravManager — Kosmetiska upplåsningar (sprint 9)"""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class CosmeticUnlock(Base):
    __tablename__ = "cosmetic_unlocks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stables.id", ondelete="CASCADE"), nullable=False)
    item_key: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="purchase", server_default="purchase")
    unlocked_at: Mapped[datetime] = mapped_column(server_default=func.now())
