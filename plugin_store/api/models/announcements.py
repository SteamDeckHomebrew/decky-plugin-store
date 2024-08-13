from datetime import datetime

from ..utils import UUID7
from .base import BaseModel


class CurrentAnnouncementResponse(BaseModel):
    class Config:
        orm_mode = True

    id: UUID7

    title: str
    text: str

    created: datetime
    updated: datetime


class AnnouncementResponse(BaseModel):
    class Config:
        orm_mode = True

    id: UUID7

    title: str
    text: str

    active: bool

    created: datetime
    updated: datetime


class AnnouncementRequest(BaseModel):
    title: str
    text: str
