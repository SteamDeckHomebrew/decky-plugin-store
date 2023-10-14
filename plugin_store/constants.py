from pathlib import Path
from enum import Enum

BASE_DIR = Path(__file__).expanduser().resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

CDN_URL = "https://cdn.tzatzikiweeb.moe/file/steam-deck-homebrew/"


class SortDirection(Enum):
    desc = "desc"
    asc = "asc"


class SortType(Enum):
    name = "name"
    date = "date"
