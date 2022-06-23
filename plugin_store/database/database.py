from unicodedata import name
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from asyncio import Lock
from .models import Base
from .models.Artifact import Artifact, Tag
from .models.Version import Version

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.engine = create_async_engine("sqlite+aiosqlite:///{}".format(self.db_path))
        self.lock = Lock()
    
    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            self.session = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)()
    
    async def insert_plugin(**kwargs):
        plugin = Artifact(
            pending = True,
            name = kwargs["name"],
            author = kwargs["author"],
            description = kwargs["description"],
            discord_id = kwargs["discord_id"],
            tags = [Tag(tag=i) for i in kwargs["tags"]]
        )
