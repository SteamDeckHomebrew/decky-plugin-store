import random

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, UTC
from hashlib import sha256
from os import getenv

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select

from database.models import Artifact, Base, Tag, Version


class FakePluginGenerator:
    def __init__(
        self,
        session: "AsyncSession",
        date: datetime | None = None,
    ):
        self.created_plugins_count = 0
        self.session = session
        self.date = datetime.now(tz=UTC) if date is None else date

    def move_date(self, seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0, weeks: int = 0):
        self.date += timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)

    async def _prepare_tags(self, tag_names):
        statement = select(Tag).where(Tag.tag.in_(tag_names)).order_by(Tag.id)
        tags = list((await self.session.execute(statement)).scalars())
        existing = [tag.tag for tag in tags]
        for tag_name in tag_names:
            if tag_name not in existing:
                tag = Tag(tag=tag_name)
                self.session.add(tag)
                tags.append(tag)

        return tags

    async def _create_plugin(
        self,
        name,
        author,
        description,
        image_path,
        tags,
        visible,
        id_=None,
    ):
        plugin = Artifact(
            name=name,
            author=author,
            description=description,
            _image_path=image_path,
            tags=tags,
            visible=visible,
        )
        if id_ is not None:
            plugin.id = id_
        self.session.add(plugin)
        await self.session.commit()
        return plugin

    async def _create_versions(self, plugin, versions):
        for version in versions:
            version = Version(
                artifact_id=plugin.id,
                name=version,
                hash=sha256(f"{plugin.id}-{version}".encode()).hexdigest(),
                created=self.date,
            )
            self.session.add(version)
            await self.session.commit()
            self.move_date(seconds=1)

    async def create(
        self,
        name: "str | None" = None,
        author: "str | None" = None,
        description: "str | None" = None,
        image: "str | None" = None,
        tags: "int | list[str] | None" = None,
        versions: "int | list[str] | None" = None,
        visible: bool = True,
    ):
        if not name:
            name = f"plugin-{self.created_plugins_count + 1}"

        if not author:
            author = f"author-of-{name}"

        if not description:
            description = f"Description of {name}"

        if tags is None:
            tags = random.randint(1, 4)

        if isinstance(tags, int):
            tags = [f"tag-{i}" for i in range(tags)]

        tag_objs = await self._prepare_tags(tags)

        plugin = await self._create_plugin(name, author, description, image, tag_objs, visible)

        if versions is None:
            versions = random.randint(1, 4)

        if isinstance(versions, int):
            versions = [f"0.{i + 1}.0" for i in range(versions)]

        await self._create_versions(plugin, versions)

        self.created_plugins_count += 1


def create_test_db_engine() -> "AsyncEngine":
    return create_async_engine(
        getenv("DB_URL"),
        pool_pre_ping=True,
        # echo=True,
    )


def create_test_db_sessionmaker(engine: "AsyncEngine") -> "sessionmaker":
    return sessionmaker(
        bind=engine,
        autoflush=False,
        future=True,
        expire_on_commit=False,
        autocommit=False,
        class_=AsyncSession,
    )


async def migrate_test_db(engine: "AsyncEngine") -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_test_db(db_sessionmaker: "sessionmaker") -> None:
    session = db_sessionmaker()
    generator = FakePluginGenerator(session, datetime(2022, 2, 25, 0, 0, 0, tzinfo=UTC))
    await generator.create(tags=["tag-1", "tag-2"], versions=["0.1.0", "0.2.0", "1.0.0"])
    generator.date = datetime(2022, 2, 25, 0, 1, 0, 0, tzinfo=UTC)
    await generator.create(image="2.png", tags=["tag-2"], versions=["1.1.0", "2.0.0"])
    generator.date = datetime(2022, 2, 25, 0, 2, 0, 0, tzinfo=UTC)
    await generator.create("third", tags=["tag-2", "tag-3"], versions=["3.0.0", "3.1.0", "3.2.0"])
    generator.date = datetime(2022, 2, 25, 0, 3, 0, 0, tzinfo=UTC)
    await generator.create(tags=["tag-1", "tag-3"], versions=["1.0.0", "2.0.0", "3.0.0", "4.0.0"])
    generator.date = datetime(2022, 2, 25, 0, 4, 0, 0, tzinfo=UTC)
    await generator.create(tags=["tag-1", "tag-2"], versions=["0.1.0", "0.2.0", "1.0.0"], visible=False)
    generator.date = datetime(2022, 2, 25, 0, 5, 0, 0, tzinfo=UTC)
    await generator.create(image="6.png", tags=["tag-2"], versions=["1.1.0", "2.0.0"], visible=False)
    generator.date = datetime(2022, 2, 25, 0, 6, 0, 0, tzinfo=UTC)
    await generator.create("seventh", tags=["tag-2", "tag-3"], versions=["3.0.0", "3.1.0", "3.2.0"], visible=False)
    generator.date = datetime(2022, 2, 25, 0, 7, 0, 0, tzinfo=UTC)
    await generator.create(tags=["tag-1", "tag-3"], versions=["1.0.0", "2.0.0", "3.0.0", "4.0.0"], visible=False)


async def prepare_test_db(
    engine: "AsyncEngine",
    db_sessionmaker: "sessionmaker",
    seed: bool = False,
) -> None:
    await migrate_test_db(engine)
    if seed:
        await seed_test_db(db_sessionmaker)


@asynccontextmanager
async def prepare_transactioned_db_session(engine: "AsyncEngine", db_sessionmaker: "sessionmaker") -> "AsyncSession":
    connection = await engine.connect()
    outer_transaction = await connection.begin()
    async_session = db_sessionmaker(bind=connection)
    # seems like for sqlite releasing last savepoint commits the whole transaction. This should fix that.
    await connection.begin_nested()
    nested = await connection.begin_nested()

    @event.listens_for(async_session.sync_session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested

        if not nested.is_active:
            nested = connection.sync_connection.begin_nested()

    yield async_session

    await outer_transaction.rollback()
    await async_session.close()
    await connection.close()
