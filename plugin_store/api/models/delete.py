from pydantic import BaseModel


class DeletePluginRequest(BaseModel):
    id: int
