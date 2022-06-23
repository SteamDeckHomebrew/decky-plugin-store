from . import Base
from sqlalchemy import Column, Integer, Text, Boolean, Table, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, selectinload

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    tag = Column(Text)

PluginTag = Table("plugin_tag", Base.metadata,
    Column("artifact_id", Integer, ForeignKey("artifacts.id")),
    Column("tag_id", Integer, ForeignKey("tags.id"))
)

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, autoincrement=True, primary_key=True)
    pending = Column(Boolean)
    name = Column(Text)
    author = Column(Text)
    description = Column(Text)
    discord_id = Column(Text)
    tags = relationship("Tags", secondary=PluginTag)

    UniqueConstraint("name")
    _query_options = [selectinload(tags)]