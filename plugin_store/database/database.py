import logging
from asyncio import Lock
from datetime import datetime
from os import getenv
from typing import Optional, TYPE_CHECKING
from uuid import UUID
from zoneinfo import ZoneInfo

from alembic import command
from alembic.config import Config
from asgiref.sync import sync_to_async
from fastapi import Depends
from sqlalchemy import asc, desc
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.sql import delete, select, update

from constants import SortDirection, SortType

from .models.announcements import Announcement
from .models.Artifact import Artifact, PluginTag, Tag
from .models.Version import Version

if TYPE_CHECKING:
    from typing import AsyncIterator, Iterable, Sequence

logger = logging.getLogger()

UTC = ZoneInfo("UTC")

db_url = getenv("DB_URL")
if not db_url:
    raise Exception("DB_URL not provided or invalid!")
async_engine = create_async_engine(
    db_url,
    pool_pre_ping=True,
    # echo=settings.ECHO_SQL,
)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, autoflush=False, future=True, expire_on_commit=False)

db_lock = Lock()


async def get_session() -> "AsyncIterator[AsyncSession]":
    try:
        yield AsyncSessionLocal()
    except SQLAlchemyError as e:
        logger.exception(e)


async def database(session: "AsyncSession" = Depends(get_session)) -> "AsyncIterator[Database]":
    db = Database(session, db_lock)
    try:
        yield db
    except Exception:
        await session.rollback()
        raise
    else:
        await session.close()


class Database:
    def __init__(self, session, lock):
        self.session = session
        self.lock = lock

    @sync_to_async()
    def init(self):
        alembic_cfg = Config("/alembic.ini")
        command.upgrade(alembic_cfg, "head")

    async def list_announcements(self, active: bool = True):
        statement = select(Announcement)
        if active:
            statement = statement.where(Announcement.active.is_(True))
        statement = statement.order_by(desc(Announcement.created))
        result = (await self.session.execute(statement)).scalars().all()
        return result or []

    async def get_announcement(self, announcement_id: UUID) -> Announcement | None:
        statement = select(Announcement).where(Announcement.id == announcement_id)
        try:
            return (await self.session.execute(statement)).scalars().first()
        except NoResultFound:
            return None

    async def create_announcement(self, title: str, text: str, active: bool) -> Announcement | None:
        nested = await self.session.begin_nested()
        async with self.lock:
            announcement = Announcement(
                title=title,
                text=text,
                active=active,
            )
            try:
                self.session.add(announcement)
            except Exception:
                await nested.rollback()
                raise
            await self.session.commit()
        return await self.get_announcement(announcement.id)

    async def update_announcement(self, announcement: Announcement, **kwargs) -> Announcement | None:
        nested = await self.session.begin_nested()
        async with self.lock:
            if "title" in kwargs:
                announcement.title = kwargs["title"]
            if "text" in kwargs:
                announcement.text = kwargs["text"]
            if "active" in kwargs:
                announcement.active = kwargs["active"]
            try:
                self.session.add(announcement)
            except Exception:
                await nested.rollback()
                raise
            await self.session.commit()
        return await self.get_announcement(announcement.id)

    async def delete_announcement(self, announcement_id: UUID) -> None:
        await self.session.execute(delete(Announcement).where(Announcement.id == announcement_id))
        await self.session.commit()

    async def prepare_tags(self, session: "AsyncSession", tag_names: list[str]) -> "list[Tag]":
        try:
            statement = select(Tag).where(Tag.tag.in_(tag_names)).order_by(Tag.id)
            tags = list((await session.execute(statement)).scalars())
            existing = [tag.tag for tag in tags]
            for tag_name in tag_names:
                if tag_name not in existing:
                    tag = Tag(tag=tag_name)
                    session.add(tag)
                    tags.append(tag)
        except Exception:
            raise
        return tags

    async def insert_artifact(
        self,
        session: "AsyncSession",
        *,
        name: "str",
        author: "str",
        description: "str",
        tags: "list[str]",
        image_path: "str | None" = None,
        id: "int | None" = None,
        visible: "bool" = True,
    ) -> "Artifact":
        nested = await session.begin_nested()
        async with self.lock:
            tag_objs = await self.prepare_tags(session, tags)
            plugin = Artifact(
                name=name,
                author=author,
                description=description,
                _image_path=image_path,
                tags=tag_objs,
                visible=visible,
            )
            if id is not None:
                plugin.id = id
            try:
                session.add(plugin)
            except Exception:
                await nested.rollback()
                raise
            await session.commit()
            return await self.get_plugin_by_id(session, plugin.id)

    async def update_artifact(self, session: "AsyncSession", plugin: "Artifact", **kwargs) -> "Artifact":
        nested = await session.begin_nested()
        async with self.lock:
            if "author" in kwargs:
                plugin.author = kwargs["author"]
            if "description" in kwargs:
                plugin.description = kwargs["description"]
            if "image_path" in kwargs:
                plugin._image_path = kwargs["image_path"]
            if "tags" in kwargs:
                plugin.tags = await self.prepare_tags(session, kwargs["tags"])
            try:
                session.add(plugin)
            except Exception:
                await nested.rollback()
                raise
            await session.commit()
        return await self.get_plugin_by_id(session, plugin.id)

    async def insert_version(
        self,
        session: "AsyncSession",
        artifact_id: int,
        name: str,
        hash: str,
        created: "datetime | None" = None,
    ) -> "Version":
        version = Version(artifact_id=artifact_id, name=name, hash=hash, created=created or datetime.now(UTC))
        async with self.lock:
            session.add(version)
            await session.commit()
        return version

    async def search(
        self,
        session: "AsyncSession",
        name: "str | None" = None,
        tags: "Iterable[str] | None" = None,
        include_hidden: "bool" = False,
        sort_by: Optional[SortType] = None,
        sort_direction: SortDirection = SortDirection.DESC,
        limit: int = 50,
        page: int = 0,
    ) -> "Sequence[Artifact]":
        statement = select(Artifact).offset(limit * page)
        if name:
            statement = statement.where(Artifact.name.like(f"%{name}%"))
        if tags:
            for tag in tags:
                statement = statement.filter(Artifact.tags.any(tag=tag))
        if not include_hidden:
            statement = statement.where(Artifact.visible.is_(True))

        if sort_direction == SortDirection.ASC:
            direction = asc
        else:
            direction = desc

        if sort_by == SortType.NAME:
            statement = statement.order_by(direction(Artifact.name))
        elif sort_by == SortType.DATE:
            statement = statement.order_by(direction(Artifact.created))
        elif sort_by == SortType.DOWNLOADS:
            statement = statement.order_by(direction(Artifact.downloads))
        else:
            statement = statement.order_by(direction(Artifact.id))

        result = (await session.execute(statement)).scalars().all()
        return result or []

    async def get_plugin_by_name(self, session: "AsyncSession", name: str) -> "Artifact | None":
        statement = select(Artifact).where(Artifact.name == name)
        try:
            return (await session.execute(statement)).scalars().first()
        except NoResultFound:
            return None

    async def get_plugin_by_id(self, session: "AsyncSession", id: int) -> "Artifact":
        statement = select(Artifact).where(Artifact.id == id)
        return (await session.execute(statement)).scalars().one()

    async def delete_plugin(self, session: "AsyncSession", id: int):
        await session.execute(delete(PluginTag).where(PluginTag.c.artifact_id == id))
        await session.execute(delete(Version).where(Version.artifact_id == id))
        await session.execute(delete(Artifact).where(Artifact.id == id))
        return await session.commit()

    async def increment_installs(
        self, session: "AsyncSession", plugin_name: str, version_name: str, isUpdate: bool
    ) -> bool:
        statement = update(Version)
        if isUpdate:
            statement = statement.values(updates=Version.updates + 1)
        else:
            statement = statement.values(downloads=Version.downloads + 1)
        plugin_id = (await session.execute(select(Artifact.id).where(Artifact.name == plugin_name))).scalar()
        if plugin_id is None:
            return False
        r = await session.execute(statement.where((Version.name == version_name) & (Version.artifact_id == plugin_id)))
        await session.commit()
        # if rowcount is zero then the version wasn't found
        return r.rowcount == 1  # type: ignore[attr-defined]
