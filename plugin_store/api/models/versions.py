from typing import Dict
from api.models.base import BaseModel

class VersionsResponse(BaseModel):
    __root__: Dict[str, str]