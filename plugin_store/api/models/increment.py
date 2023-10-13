from fastapi import UploadFile
from pydantic import BaseModel, HttpUrl

class SubmitIncrementRequest(BaseModel):
    name: str
    isUpdate: bool # uncertain if this is valid