from datetime import datetime
from urllib.parse import quote

from sqlalchemy import Boolean, Column, ForeignKey, func, Integer, select, Table, Text, UniqueConstraint
from sqlalchemy.orm import column_property, Mapped, relationship

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

    id: Mapped[int] = Column(Integer, autoincrement=True, primary_key=True)
    name: Mapped[str] = Column(Text)
    author: Mapped[str] = Column(Text)
    description: Mapped[str] = Column(Text)
    _image_path: Mapped[str | None] = Column("image_path", Text, nullable=True)
    tags: "Mapped[list[Tag]]" = relationship(
        "Tag", secondary=PluginTag, cascade="all, delete", order_by="Tag.tag", lazy="selectin"
    )
    versions: "Mapped[list[Version]]" = relationship(
        "Version", cascade="all, delete", lazy="selectin", order_by="Version.created.desc(), Version.id.asc()"
    )
    visible: Mapped[bool] = Column(Boolean, default=True)

    # Properties computed from relations
    downloads: Mapped[int] = column_property(
        select(func.sum(Version.downloads)).where(Version.artifact_id == id).correlate_except(Version).scalar_subquery()
    )
    updates: Mapped[int] = column_property(
        select(func.sum(Version.updates)).where(Version.artifact_id == id).correlate_except(Version).scalar_subquery()
    )

    created: Mapped[datetime] = column_property(
        select(func.min(Version.created)).where(Version.artifact_id == id).correlate_except(Version).scalar_subquery()
    )
    updated: Mapped[datetime] = column_property(
        select(func.max(Version.created)).where(Version.artifact_id == id).correlate_except(Version).scalar_subquery()
    )

    UniqueConstraint("name")

    @property
    def image_url(self):
        return f"{constants.CDN_URL}{self.image_path}"

    @property
    def image_path(self):
        if self._image_path is not None:
            return self._image_path
        return f"artifact_images/{quote(self.name)}.png"
