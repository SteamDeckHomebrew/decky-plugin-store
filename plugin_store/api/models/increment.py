from fastapi import UploadFile
from pydantic import BaseModel, HttpUrl

class SubmitIncrementRequest(BaseModel):
    name: str
    isUpdate: bool