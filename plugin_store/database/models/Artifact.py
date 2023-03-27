from datetime import datetime
from urllib.parse import quote

from sqlalchemy import Boolean, Column, ForeignKey, func, Integer, select, Table, Text, UniqueConstraint
from sqlalchemy.orm import column_property, relationship

import constants

from .Base import Base
from .Version import Version


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("tag", name="unique_tag_tag"),)

    id = Column(Integer, primary_key=True)
    tag = Column(Text)


PluginTag = Table(
    "plugin_tag",
    Base.metadata,
    Column("artifact_id", Integer, ForeignKey("artifacts.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)


class Artifact(Base):
    __tablename__ = "artifacts"

    id: int = Column(Integer, autoincrement=True, primary_key=True)
    name: str = Column(Text)
    author: str = Column(Text)
    description: str = Column(Text)
    tags: "list[Tag]" = relationship(
        "Tag", secondary=PluginTag, cascade="all, delete", order_by="Tag.tag", lazy="selectin"
    )
    versions: "list[Version]" = relationship(
        "Version", cascade="all, delete", lazy="selectin", order_by="Version.created.desc()"
    )
    visible: bool = Column(Boolean, default=True)

    created: datetime = column_property(
        select(func.min(Version.created)).where(Version.artifact_id == id).correlate_except(Version).scalar_subquery()
    )
    updated: datetime = column_property(
        select(func.max(Version.created)).where(Version.artifact_id == id).correlate_except(Version).scalar_subquery()
    )

    UniqueConstraint("name")

    @property
    def image_url(self):
        return f"{constants.CDN_URL}{self.image_path}"

    @property
    def image_path(self):
        return f"artifact_images/{quote(self.name)}.png"
