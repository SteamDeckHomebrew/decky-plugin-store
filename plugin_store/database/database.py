from typing import TYPE_CHECKING

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.sql import select, insert, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy import or_
from asyncio import Lock
from datetime import datetime

from .models import Base
from .models.Artifact import Artifact, Tag, PluginTag
from .models.Version import Version

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional, Union

class Database:
    def __init__(self, db_path: "Union[str, Path]"):
        self.db_path = db_path
        self.engine = create_async_engine("sqlite+aiosqlite:///{}".format(self.db_path))
        self.lock = Lock()
        self.maker = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
    
    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    class _FakeObj:
        def __init__(self, id: int):
            self.id = id

    async def _get_or_insert(self, session: "AsyncSession", t: "Base", **kwargs):
        statement = select(t)
        for i,v in kwargs.items():
            statement = statement.where(getattr(t, i) == v)
        res = (await session.execute(statement)).scalars().first()
        if res:
            return res
        statement = insert(t).values(**kwargs)
        res = await session.execute(statement)
        return self._FakeObj(res.inserted_primary_key[0])

    async def insert_artifact(self, session: "AsyncSession", **kwargs) -> "Artifact":
        nested = await session.begin_nested()
        plugin = Artifact(
            name = kwargs["name"],
            author = kwargs["author"],
            description = kwargs["description"],
            tags = [Tag(tag=i) for i in kwargs["tags"]]
        )
        if "id" in kwargs:
            plugin.id = kwargs["id"]
        async with self.lock:
            session.add(plugin)
            try:
                for tag in kwargs.get("tags", []):
                    await self._get_or_insert(session, Tag, tag=tag)
                    # await self.session.execute(insert(PluginTag).values(artifact_id=plugin.id, tag_id=res.id)) for some reason this leads to duplicating tags, but it works fine without it
            except Exception as e:
                await nested.rollback()
                raise e
            await session.commit()
            return await self.get_plugin_by_id(session, plugin.id)
    
    async def insert_version(self, session: "AsyncSession", artifact_id: int, **kwargs) -> "Version":
        version = Version(
            artifact_id=artifact_id,
            name=kwargs["name"],
            hash=kwargs["hash"],
            added_on=datetime.now()
        )
        async with self.lock:
            session.add(version)
            await session.commit()
        return version

    async def search(self, session: "AsyncSession", name=None, tags=None, limit=50, page=0) -> list["Artifact"]:
        statement = select(Artifact).options(*Artifact._query_options).offset(limit * page)
        if name:
            name_select = select(Artifact).where(Artifact.name.like(f"%{name}%")).options(*Artifact._query_options)
            content = (await session.execute(name_select)).scalars().all()
            if not content:
                return []
            statement = statement.filter(or_(*[(Artifact.id == i.id) for i in content]))
        if tags:
            for tag in tags:
                statement = statement.filter(Artifact.tags.any(tag=tag))
        result = (await session.execute(statement)).scalars().all()
        return result or []

    async def get_plugin_by_name(self, session: "AsyncSession", name: str) -> "Optional[Artifact]":
        statement = select(Artifact).options(*Artifact._query_options).where(Artifact.name == name)
        try:
            return (await session.execute(statement)).scalars().first()
        except NoResultFound:
            return None
    
    async def get_plugin_by_id(self, session: "AsyncSession", id: int) -> "Optional[Artifact]":
        statement = select(Artifact).options(*Artifact._query_options).where(Artifact.id == id)
        try:
            return (await session.execute(statement)).scalars().first()
        except NoResultFound:
            return None
    
    async def delete_plugin(self, session: "AsyncSession", id: int):
        await session.execute(delete(PluginTag).where(PluginTag.c.artifact_id == id))
        await session.execute(delete(Version).where(Version.artifact_id == id))
        await session.execute(delete(Artifact).where(Artifact.id == id))
        return await session.commit()