from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from api.dependencies import auth_token
from constants import TEMPLATES_DIR

INDEX_PAGE = (TEMPLATES_DIR / "plugin_browser.html").read_text()

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_PAGE


@router.post("/__auth", response_model=str, dependencies=[Depends(auth_token)])
async def auth_check():
    return "Success"
