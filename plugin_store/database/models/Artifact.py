from urllib.parse import quote

from sqlalchemy import Column, ForeignKey, Integer, Table, Text, UniqueConstraint
from sqlalchemy.orm import relationship, selectinload

import constants

from . import Base


class Tag(Base):
    __tablename__ = "tags"

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

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Text)
    author = Column(Text)
    description = Column(Text)
    tags = relationship("Tag", secondary=PluginTag, cascade="all, delete", lazy="selectin")
    versions = relationship("Version", cascade="all, delete", lazy="selectin")

    UniqueConstraint("name")

    @property
    def image_url(self):
        return f"{constants.CDN_URL}/{self.image_path}"

    @property
    def image_path(self):
        return f"artifact_images/{quote(self.name)}.png"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "author": self.author,
            "description": self.description,
            "image_url": self.image_url,
            "tags": [i.tag for i in self.tags],
            "versions": [i.to_dict() for i in reversed(self.versions)],
        }


Artifact._query_options = [selectinload(Artifact.tags), selectinload(Artifact.versions)]
