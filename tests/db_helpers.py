import random
from datetime import datetime, timedelta, UTC
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Artifact, Tag, Version


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
        id=None,
    ):
        plugin = Artifact(
            name=name,
            author=author,
            description=description,
            _image_path=image_path,
            tags=tags,
            visible=visible,
        )
        if id is not None:
            plugin.id = id
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
