from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text

from . import Base


class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"))
    name = Column(Text)
    hash = Column(Text)
    added_on = Column(DateTime)

    def to_dict(self):
        return {
            "name": self.name,
            "hash": self.hash,
        }
