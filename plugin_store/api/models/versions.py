from typing import Dict, List
from api.models.base import BaseModel

class VersionsResponse(BaseModel):
    __root__: Dict[str, List[str]]