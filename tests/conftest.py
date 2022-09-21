import random
from hashlib import sha256
from os import getenv
from pathlib import Path
from string import ascii_lowercase
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from aiohttp import FormData
from pytest_mock import MockFixture

import main

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from typing import Callable, Optional, Union

    from aiohttp.test_utils import TestClient
    from aiohttp.web_app import Application
    from sqlalchemy.ext.asyncio import AsyncSession

    from database.database import Database

APP_PATH = Path("../app").absolute()


@pytest.fixture(scope="session", autouse=True)
def mock_external_services(session_mocker: "MockFixture"):
    session_mocker.patch("main.b2_upload")
    session_mocker.patch("main.AsyncDiscordWebhook", new=session_mocker.AsyncMock)


@pytest.fixture()
def plugin_store() -> "main.PluginStore":
    return main.PluginStore()


# Client for aiohttp server
@pytest_asyncio.fixture()
async def client_unauth(
    aiohttp_client: "Callable[[Application], Awaitable[TestClient]]",
    plugin_store: "main.PluginStore",
) -> "TestClient":
    return await aiohttp_client(plugin_store.server)


@pytest_asyncio.fixture()
async def client_auth(client_unauth: "TestClient") -> "TestClient":
    client_unauth.session.headers["Authorization"] = getenv("SUBMIT_AUTH_KEY")
    return client_unauth


@pytest_asyncio.fixture()
async def db(plugin_store: "main.PluginStore") -> "Database":
    await plugin_store.database.init()
    return plugin_store.database


class FakePluginGenerator:
    def __init__(self, db: "Database", session: "AsyncSession"):
        self.created_plugins_count = 0
        self.db = db
        self.session = session

    async def create(
        self,
        name: "Optional[str]" = None,
        author: "Optional[str]" = None,
        description: "Optional[str]" = None,
        tags: "Optional[Union[int, list[str]]]" = None,
        versions: "Optional[Union[int, list[str], list[dict]]]" = None,
    ):
        if not name:
            name = "".join(random.choices(ascii_lowercase, k=12))

        if not author:
            author = f"author-of-{name}"

        if not description:
            description = f"Description of {name}"

        if tags is None:
            tags = random.randint(1, 4)

        if isinstance(tags, int):
            tags = [f"tag-{i}" for i in range(tags)]

        plugin = await self.db.insert_artifact(
            session=self.session,
            name=name,
            author=author,
            description=description,
            tags=tags,
        )

        if versions is None:
            versions = random.randint(1, 4)

        if isinstance(versions, int):
            versions = [f"0.{i}.0" for i in range(versions)]

        for version in versions:
            if isinstance(version, str):
                version = {"name": version, "hash": sha256(f"{plugin.id}-{version}".encode()).hexdigest()}

            await self.db.insert_version(self.session, plugin.id, **version)

        self.created_plugins_count += 1


@pytest_asyncio.fixture()
async def seed_db(db):
    session = db.maker()
    generator = FakePluginGenerator(db, session)
    await generator.create(name="plugin-1", tags=["tag-1", "tag-2"], versions=["0.1.0", "0.2.0", "1.0.0"])
    await generator.create(name="plugin-2", tags=["tag-1", "tag-3"], versions=["1.1.0", "2.0.0"])
    await generator.create(name="plugin-3", tags=["tag-2", "tag-3"], versions=["3.0.0", "3.1.0", "3.2.0"])
    await generator.create(name="plugin-4", tags=["tag-1"], versions=["1.0.0", "2.0.0", "3.0.0", "4.0.0"])
    session.commit()

    return db


@pytest.fixture()
def plugin_submit_data(request: "pytest.FixtureRequest") -> "FormData":
    data = FormData(
        {
            "name": request.param,
            "author": "plugin-author-of-new-plugin",
            "description": "Description of our brand new plugin!",
            "tags": "tag-1,new-tag-2",
            "version_name": "2.0.0",
            "image": "https://example.com/image.png",
        },
    )
    data.add_field(
        "file",
        "this-is-a-test-file-content",
        filename="new-release.bin",
        content_type="application/x-binary",
    )
    return data


@pytest.fixture()
def index_template():
    return (APP_PATH / "templates/plugin_browser.html").read_text()
