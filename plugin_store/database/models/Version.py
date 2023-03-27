from sqlalchemy import Column, ForeignKey, Integer, Text

from ..utils import TZDateTime
from .Base import Base


class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"))
    name = Column(Text)
    hash = Column(Text)
    created = Column("added_on", TZDateTime)
