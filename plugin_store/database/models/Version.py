from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint

import constants

from ..utils import TZDateTime
from .Base import Base


class Version(Base):
    __tablename__ = "versions"
    __table_args__ = (UniqueConstraint("artifact_id", "name", name="unique_version_artifact_id_name"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"))
    name = Column(Text)
    hash = Column(Text)
    file_field = Column("file", Text, nullable=True)
    downloads = Column(Integer, default=0, nullable=False)
    updates = Column(Integer, default=0, nullable=False)

    created = Column("added_on", TZDateTime)

    @property
    def file_url(self):
        return f"{constants.CDN_URL}{self.download_path}"

    @property
    def file(self):
        return f"artifact_images/{self.hash}.zip"
