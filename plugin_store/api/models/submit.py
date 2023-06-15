from fastapi import UploadFile
from pydantic import BaseModel, HttpUrl

from api.models.base import BasePluginResponse


class SubmitProductRequest(BaseModel):
    name: str
    author: str
    description: str
    tags: list[str]  # Comma separated values
    version_name: str
    image: HttpUrl
    file: UploadFile
    force: bool = False


class SubmitProductResponse(BasePluginResponse):
    pass
