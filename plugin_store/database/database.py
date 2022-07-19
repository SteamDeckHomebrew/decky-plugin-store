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

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.engine = create_async_engine("sqlite+aiosqlite:///{}".format(self.db_path))
        self.lock = Lock()
    
    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            self.session = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)()

    class _FakeObj:
        def __init__(self, id):
            self.id = id

    async def _get_or_insert(self, t, **kwargs):
        statement = select(t)
        for i,v in kwargs.items():
            statement = statement.where(getattr(t, i) == v)
        res = (await self.session.execute(statement)).scalars().first()
        if res:
            print("found")
            return res
        statement = insert(t).values(**kwargs)
        res = await self.session.execute(statement)
        print("not found")
        return self._FakeObj(res.inserted_primary_key[0])

    async def _insert_if_not_already(self, t, **kwargs):
        statement = select(t)
        for i,v in kwargs.items():
            statement = statement.where(getattr(t.c, i) == v)
        res = (await self.session.execute(statement)).scalars().first()
        if res:
            print("found insert")
            return res
        statement = insert(t).values(**kwargs)
        res = await self.session.execute(statement)
        print("not found insert")
        # return self._FakeObj(res.inserted_primary_key[0])

    async def insert_artifact(self, **kwargs):
        nested = await self.session.begin_nested()
        plugin = Artifact(
            name = kwargs["name"],
            author = kwargs["author"],
            description = kwargs["description"],
            tags = [Tag(tag=i) for i in kwargs["tags"]]
        )
        if "id" in kwargs:
            plugin.id = kwargs["id"]
        async with self.lock:
            self.session.add(plugin)
            try:
                for tag in kwargs.get("tags", []):
                    res = await self._get_or_insert(Tag, tag=tag)
                    print("tag res for " + str(plugin.id) + " : " + str(res.id) + " on tag" + tag)
                    await self._insert_if_not_already(PluginTag, artifact_id=plugin.id, tag_id=res.id)
            except Exception as e:
                await nested.rollback()
                raise e
            await self.session.commit()
            return await self.get_plugin_by_id(plugin.id)
    
    async def insert_version(self, artifact_id, **kwargs):
        version = Version(
            artifact_id=artifact_id,
            name=kwargs["name"],
            hash=kwargs["hash"],
            added_on=datetime.now()
        )
        async with self.lock:
            self.session.add(version)
            await self.session.commit()
        return version

    async def search(self, name=None, tags=None, limit=50, page=0):
        statement = select(Artifact).options(*Artifact._query_options).offset(limit * page)
        if name:
            name_select = select(Artifact).where(Artifact.name.like(f"%{name}%")).options(*Artifact._query_options)
            content = (await self.session.execute(name_select)).scalars().all()
            if not content:
                return []
            statement = statement.filter(or_(*[(Artifact.id == i.id) for i in content]))
        if tags:
            for tag in tags:
                statement = statement.filter(Artifact.tags.any(tag=tag))
        result = (await self.session.execute(statement)).scalars().all()
        return result or []

    async def get_plugin_by_name(self, name):
        statement = select(Artifact).options(*Artifact._query_options).where(Artifact.name == name)
        try:
            return (await self.session.execute(statement)).scalars().first()
        except NoResultFound:
            return None
    
    async def get_plugin_by_id(self, id):
        statement = select(Artifact).options(*Artifact._query_options).where(Artifact.id == id)
        try:
            return (await self.session.execute(statement)).scalars().first()
        except NoResultFound:
            return None
    
    async def delete_plugin(self, id):
        query = delete(PluginTag).where(PluginTag.c.artifact_id == id)
        print(query)
        await self.session.execute(query, {"artifact_id_1": id})
        await self.session.execute(delete(Version).where(Version.artifact_id == id))
        await self.session.execute(delete(Artifact).where(Artifact.id == id))
        return await self.session.commit()