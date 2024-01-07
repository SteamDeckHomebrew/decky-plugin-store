from datetime import datetime, UTC
from os import getenv
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import main
from api import database as db_dependency
from database.database import Database
from database.models import Base
from db_helpers import FakePluginGenerator

if TYPE_CHECKING:
    from typing import AsyncIterator

    from fastapi import FastAPI

APP_PATH = Path("./plugin_store").absolute()
TESTS_PATH = Path(__file__).expanduser().resolve().parent
DUMMY_DATA_PATH = TESTS_PATH / "dummy_data"


@pytest.fixture(scope="session", autouse=True)
def mock_external_services(session_mocker: "MockFixture"):
    session_mocker.patch("cdn.b2_upload")
    session_mocker.patch(
        "cdn.fetch_image",
        return_value=((DUMMY_DATA_PATH / "plugin-image.png").read_bytes(), "image/png"),
    )
    session_mocker.patch("discord.AsyncDiscordWebhook", new=session_mocker.AsyncMock)


@pytest.fixture(scope="session", autouse=True)
def mock_constants(session_mocker: "MockFixture"):
    """
    Auto-mocking some constants to make sure they are used instead of hardcoded values.
    """
    session_mocker.patch("constants.CDN_URL", new="hxxp://fake.domain/")


@pytest.fixture()
def plugin_store(db: "Database") -> "FastAPI":
    main.app.dependency_overrides[db_dependency] = lambda: db
    return main.app


# Client for aiohttp server
@pytest_asyncio.fixture()
async def client_unauth(
    plugin_store: "FastAPI",
) -> "AsyncIterator[AsyncClient]":
    async with AsyncClient(app=plugin_store, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture()
async def client_auth(client_unauth: "AsyncClient") -> "AsyncClient":
    client_unauth.headers["Authorization"] = getenv("SUBMIT_AUTH_KEY", "")
    return client_unauth


@pytest.fixture()
def db_engine():
    return create_async_engine(
        getenv("DB_URL"),
        pool_pre_ping=True,
        # echo=settings.ECHO_SQL,
    )


@pytest.fixture()
def db_sessionmaker(db_engine):
    return sessionmaker(bind=db_engine, autoflush=False, future=True, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture()
async def _migrate_db(db_engine):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture()
async def db(_migrate_db: None, db_sessionmaker: sessionmaker, mocker: "MockFixture") -> "Database":
    return Database(db_sessionmaker(), lock=mocker.MagicMock())


@pytest_asyncio.fixture()
async def seed_db(db: "Database", db_sessionmaker: "sessionmaker") -> "Database":
    session = db_sessionmaker()
    generator = FakePluginGenerator(session, datetime(2022, 2, 25, 0, 0, 0, tzinfo=UTC))
    await generator.create(tags=["tag-1", "tag-2"], versions=["0.1.0", "0.2.0", "1.0.0"])
    generator.date = datetime(2022, 2, 25, 0, 1, 0, 0, tzinfo=UTC)
    await generator.create(image="2.png", tags=["tag-2"], versions=["1.1.0", "2.0.0"])
    generator.date = datetime(2022, 2, 25, 0, 2, 0, 0, tzinfo=UTC)
    await generator.create("third", tags=["tag-2", "tag-3"], versions=["3.0.0", "3.1.0", "3.2.0"])
    generator.date = datetime(2022, 2, 25, 0, 3, 0, 0, tzinfo=UTC)
    await generator.create(tags=["tag-1", "tag-3"], versions=["1.0.0", "2.0.0", "3.0.0", "4.0.0"])
    generator.date = datetime(2022, 2, 25, 0, 4, 0, 0, tzinfo=UTC)
    await generator.create(tags=["tag-1", "tag-2"], versions=["0.1.0", "0.2.0", "1.0.0"], visible=False)
    generator.date = datetime(2022, 2, 25, 0, 5, 0, 0, tzinfo=UTC)
    await generator.create(image="6.png", tags=["tag-2"], versions=["1.1.0", "2.0.0"], visible=False)
    generator.date = datetime(2022, 2, 25, 0, 6, 0, 0, tzinfo=UTC)
    await generator.create("seventh", tags=["tag-2", "tag-3"], versions=["3.0.0", "3.1.0", "3.2.0"], visible=False)
    generator.date = datetime(2022, 2, 25, 0, 7, 0, 0, tzinfo=UTC)
    await generator.create(tags=["tag-1", "tag-3"], versions=["1.0.0", "2.0.0", "3.0.0", "4.0.0"], visible=False)

    return db


@pytest.fixture()
def plugin_submit_data(request: "pytest.FixtureRequest") -> "tuple[dict, dict]":
    data = {
        "name": request.param,
        "author": "plugin-author-of-new-plugin",
        "description": "Description of our brand new plugin!",
        "tags": "tag-1,new-tag-2",
        "version_name": "2.0.0",
        "image": "https://example.com/image.png",
    }
    files = {
        "file": ("new-release.bin", b"this-is-a-test-file-content", "application/x-binary"),
    }
    return data, files


@pytest.fixture()
def index_template():
    return (APP_PATH / "templates/plugin_browser.html").read_text()
