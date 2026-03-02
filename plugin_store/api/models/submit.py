from enum import Enum

from fastapi import UploadFile
from pydantic import BaseModel, HttpUrl

from api.models.base import BasePlugin, BasePluginResponse
from api.utils import UUID7

class ArtifactAction(Enum):
    INSERT = 0
    UPDATE = 1

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

class UploadURLResponse(BaseModel):
    contextId: UUID7
    uploadUrl: str
    authToken: str

class PluginSubmitContext(SubmitProductRequest):
    id: UUID7
    plugin: BasePlugin
    artifactAction: ArtifactAction

class FinalizeSubmissionRequest(BaseModel):
    contextId: UUID7
    contentHash: str