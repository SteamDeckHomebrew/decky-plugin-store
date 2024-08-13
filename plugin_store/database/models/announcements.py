from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Boolean, Column, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..utils import TZDateTime, uuid7
from .Base import Base

UTC = ZoneInfo("UTC")


def utcnow() -> datetime:
    return datetime.now(UTC)


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)

    title: Mapped[str] = Column(Text, nullable=False)
    text: Mapped[str] = Column(Text, nullable=False)

    active: Mapped[bool] = Column(Boolean, nullable=False)

    created: Mapped[datetime] = Column(TZDateTime, nullable=False, default=utcnow)
    updated: Mapped[datetime] = Column(TZDateTime, nullable=False, default=utcnow, onupdate=utcnow)
