from typing import Annotated

import fastapi
from fastapi import APIRouter, Depends

from database.database import database, Database
from database.models import Announcement

from ..dependencies import auth_token
from ..models import announcements as api_announcements
from ..utils import UUID7

router = APIRouter()


@router.get(
    "/v1/announcements",
    dependencies=[Depends(auth_token)],
    response_model=list[api_announcements.AnnouncementResponse],
)
async def list_announcements(
    db: Annotated["Database", Depends(database)],
):
    return await db.list_announcements(active=False)


@router.post(
    "/v1/announcements",
    dependencies=[Depends(auth_token)],
    response_model=api_announcements.AnnouncementResponse,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def create_announcement(
    db: Annotated["Database", Depends(database)],
    announcement: api_announcements.AnnouncementRequest,
):
    return await db.create_announcement(title=announcement.title, text=announcement.text, active=announcement.active)


@router.get("/v1/announcements/-/current", response_model=list[api_announcements.CurrentAnnouncementResponse])
async def list_current_announcements(
    db: Annotated["Database", Depends(database)],
):
    return await db.list_announcements()


@router.get(
    "/v1/announcements/{announcement_id}",
    dependencies=[Depends(auth_token)],
    response_model=api_announcements.AnnouncementResponse,
)
async def get_announcement(
    db: Annotated["Database", Depends(database)],
    announcement_id: UUID7,
):
    return await db.get_announcement(announcement_id)


@router.put(
    "/v1/announcements/{announcement_id}",
    dependencies=[Depends(auth_token)],
    response_model=api_announcements.AnnouncementResponse,
)
async def update_announcement(
    db: Annotated["Database", Depends(database)],
    existing_announcement: Annotated["Announcement", Depends(get_announcement)],
    new_announcement: api_announcements.AnnouncementRequest,
):
    return await db.update_announcement(
        existing_announcement,
        title=new_announcement.title,
        text=new_announcement.text,
        active=new_announcement.active,
    )


@router.delete(
    "/v1/announcements/{announcement_id}",
    dependencies=[Depends(auth_token)],
    status_code=fastapi.status.HTTP_204_NO_CONTENT,
)
async def delete_announcement(
    db: Annotated["Database", Depends(database)],
    announcement_id: UUID7,
):
    await db.delete_announcement(announcement_id)
