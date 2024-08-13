from os import getenv
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pytest_mock import MockFixture
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

import main
from api import database as db_dependency
from database.database import Database
from db_helpers import (
    create_test_db_engine,
    create_test_db_sessionmaker,
    prepare_test_db,
    prepare_transactioned_db_session,
)

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
    discord_mock = session_mocker.patch("discord.AsyncDiscordWebhook", new=session_mocker.AsyncMock)
    discord_mock.add_embed = session_mocker.Mock()


@pytest.fixture(scope="session", autouse=True)
def mock_constants(session_mocker: "MockFixture"):
    """
    Auto-mocking some constants to make sure they are used instead of hardcoded values.
    """
    session_mocker.patch("constants.CDN_URL", new="hxxp://fake.domain/")


@pytest.fixture()
def plugin_store() -> "FastAPI":
    return main.app


# Client for aiohttp server
@pytest_asyncio.fixture()
async def client_unauth(
    plugin_store: "FastAPI",
) -> "AsyncIterator[AsyncClient]":
    async with AsyncClient(
        base_url="http://test",
        transport=ASGITransport(app=plugin_store),  # type: ignore[arg-type]
    ) as client:
        yield client


@pytest_asyncio.fixture()
async def client_auth(client_unauth: "AsyncClient") -> "AsyncClient":
    client_unauth.headers["Authorization"] = getenv("SUBMIT_AUTH_KEY", "")
    return client_unauth


@pytest_asyncio.fixture(scope="session")
async def seed_db_engine() -> tuple["AsyncEngine", "async_sessionmaker"]:
    engine = create_test_db_engine()
    db_sessionmaker = create_test_db_sessionmaker(engine)
    await prepare_test_db(engine, db_sessionmaker, True)
    return engine, db_sessionmaker


@pytest.fixture(scope="session")
def seed_db_sessionmaker(seed_db_engine: tuple["AsyncEngine", "sessionmaker"]) -> "sessionmaker":
    return seed_db_engine[1]


@pytest_asyncio.fixture()
async def seed_db_session(seed_db_engine: tuple["AsyncEngine", "sessionmaker"]) -> "AsyncIterator[AsyncSession]":
    async with prepare_transactioned_db_session(*seed_db_engine) as session:
        yield session


@pytest_asyncio.fixture()
async def seed_db(plugin_store: "FastAPI", seed_db_session: "AsyncSession", mocker: "MockFixture") -> "Database":
    database = Database(seed_db_session, lock=mocker.MagicMock())
    main.app.dependency_overrides[db_dependency] = lambda: database
    return database


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


@pytest.fixture()
def _mock_uuidv7_generation(mocker: "MockFixture") -> None:
    """
    Mocking UUID generation randomness

    Random generator for UUID will return 0x11, so the UUID will be predictable as long as you also freeze the time.
    UUIDs will still increment, as the generator keeps the count of generated UUIDs in a single time tick and increments
    it by 1 at 5th byte, so for 1st UUID the last segment will be `111111111111`, 2nd UUID will have `111211111111` etc.
    """

    def urandom_side_effect(size):
        return b"\x11" * size

    mocker.patch("database.utils.os.urandom", side_effect=urandom_side_effect)
