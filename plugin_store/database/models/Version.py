from sqlite3 import Date
from . import Base
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime

class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"))
    name = Column(Text)
    hash = Column(Text)
    added_on = Column(DateTime)