from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Optional

    from aiohttp import FormData
    from aiohttp.test_utils import TestClient

    from database.database import Database


@pytest.mark.asyncio
@pytest.mark.parametrize("client", [pytest.lazy_fixture("client_unauth"), pytest.lazy_fixture("client_auth")])
async def test_index_endpoint(client: "TestClient", index_template: str):
    response = await client.get("/")
    assert response.status == 200
    assert await response.text() == index_template


@pytest.mark.asyncio
@pytest.mark.parametrize("client", [pytest.lazy_fixture("client_unauth"), pytest.lazy_fixture("client_auth")])
async def test_plugins_list_endpoint(seed_db: "Database", client: "TestClient"):
    response = await client.get("/plugins")
    assert response.status == 200
    assert await response.json() == [
        {
            "id": 1,
            "name": "plugin-1",
            "author": "author-of-plugin-1",
            "description": "Description of plugin-1",
            "tags": ["tag-1", "tag-2"],
            "image_url": "hxxp://fake.domain/artifact_images/plugin-1.png",
            "versions": [
                {"name": "1.0.0", "hash": "f06b77407d0ef08f5667591ab386eeff2090c340f3eadf76006db6d1ac721029"},
                {"name": "0.2.0", "hash": "750e557099102527b927be4b9e79392c8f4e011d8a5848480afb61fc0de4f5af"},
                {"name": "0.1.0", "hash": "44733735485ece810402fff9e7a608a49039c0b363e52ff62d07b84ab2b40b06"},
            ],
        },
        {
            "id": 2,
            "name": "plugin-2",
            "author": "author-of-plugin-2",
            "description": "Description of plugin-2",
            "tags": ["tag-1", "tag-3"],
            "image_url": "hxxp://fake.domain/artifact_images/plugin-2.png",
            "versions": [
                {"name": "2.0.0", "hash": "56635138a27a6b0c57f0f06cdd58eadf58fff966516c38fca530e2d0f12a3190"},
                {"name": "1.1.0", "hash": "aeee42b51db3d73c6b75c08ccd46feff21b6de5f41bf1494d147471df850d947"},
            ],
        },
        {
            "id": 3,
            "name": "plugin-3",
            "author": "author-of-plugin-3",
            "description": "Description of plugin-3",
            "tags": ["tag-2", "tag-3"],
            "image_url": "hxxp://fake.domain/artifact_images/plugin-3.png",
            "versions": [
                {"name": "3.2.0", "hash": "ec2516b144cb429b1473104efcbe345da2b82347fbbb587193a22429a0dc6ab6"},
                {"name": "3.1.0", "hash": "8d9a561a9fc5c7509b5fe0e54213641e502e3b1e456af34cc44aa0a526f85f9b"},
                {"name": "3.0.0", "hash": "9463611d748129d063f697ec7bdd770b7d5b82c50b93582e31e6440236ba8f66"},
            ],
        },
        {
            "id": 4,
            "name": "plugin-4",
            "author": "author-of-plugin-4",
            "description": "Description of plugin-4",
            "tags": ["tag-1"],
            "image_url": "hxxp://fake.domain/artifact_images/plugin-4.png",
            "versions": [
                {"name": "4.0.0", "hash": "8eee479a02359eeb0f30f86f0bec493ba7b31ff738509a3df0f5261dcad8f45f"},
                {"name": "3.0.0", "hash": "bb70c8d12deee43fb3f2529807b132432c63253c9d27cb9f15f3c4ceae5cfc62"},
                {"name": "2.0.0", "hash": "02dd930214f64c3694122435b8a58641da279c83cd9beb9b47adf5173e07e6e5"},
                {"name": "1.0.0", "hash": "51ab66013d901f12a45142248132c0c98539c749b6a3b341ab4da2b9df4cdc09"},
            ],
        },
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("client", "return_code"),
    [(pytest.lazy_fixture("client_unauth"), 403), (pytest.lazy_fixture("client_auth"), 200)],
)
async def test_auth_endpoint(client: "TestClient", return_code: int):
    response = await client.post("/__auth")
    assert response.status == return_code


@pytest.mark.asyncio
async def test_submit_endpoint_requires_auth(client_unauth: "TestClient"):
    response = await client_unauth.post("/__submit")
    assert response.status == 403


@pytest.mark.parametrize(
    ("db_fixture", "plugin_submit_data", "name", "return_code", "resulting_versions", "error_msg"),
    [
        (
            pytest.lazy_fixture("db"),
            "new-plugin",
            "new-plugin",
            201,
            [{"name": "2.0.0", "hash": "378d3213bf3c5d1924891c05659425e7d62bb786665cb2eb5c88564a327b03c7"}],
            None,
        ),
        (
            pytest.lazy_fixture("seed_db"),
            "plugin-1",
            "plugin-1",
            201,
            [
                {"name": "2.0.0", "hash": "378d3213bf3c5d1924891c05659425e7d62bb786665cb2eb5c88564a327b03c7"},
                {"name": "1.0.0", "hash": "f06b77407d0ef08f5667591ab386eeff2090c340f3eadf76006db6d1ac721029"},
                {"name": "0.2.0", "hash": "750e557099102527b927be4b9e79392c8f4e011d8a5848480afb61fc0de4f5af"},
                {"name": "0.1.0", "hash": "44733735485ece810402fff9e7a608a49039c0b363e52ff62d07b84ab2b40b06"},
            ],
            None,
        ),
        (pytest.lazy_fixture("seed_db"), "plugin-2", "plugin-2", 400, [], "Version already exists"),
    ],
    ids=["creates_new_plugin", "uploads_new_version", "blocks_overriding_existing_version"],
    indirect=["plugin_submit_data"],
)
@pytest.mark.asyncio
async def test_submit_endpoint(
    client_auth: "TestClient",
    db_fixture: "Database",
    plugin_submit_data: "FormData",
    name: str,
    return_code: int,
    resulting_versions: list[dict],
    error_msg: "Optional[str]",
):
    response = await client_auth.post("/__submit", data=plugin_submit_data)
    assert response.status == return_code
    if return_code >= 400:
        assert (await response.json())["message"] == error_msg
    else:
        assert await response.json() == {
            "id": 1,
            "name": name,
            "author": "plugin-author-of-new-plugin",
            "description": "Description of our brand new plugin!",
            "tags": ["tag-1", "new-tag-2"],
            "image_url": f"hxxp://fake.domain/artifact_images/{name}.png",
            "versions": resulting_versions,
        }

        session = db_fixture.maker()
        plugin = await db_fixture.get_plugin_by_id(session, 1)

        assert plugin.name == name
        assert plugin.author == "plugin-author-of-new-plugin"
        assert plugin.description == "Description of our brand new plugin!"
        assert len(plugin.tags) == 2
        assert plugin.tags[0].tag == "tag-1"
        assert plugin.tags[1].tag == "new-tag-2"
        assert len(plugin.versions) == len(resulting_versions)
        for actual, expected in zip(plugin.versions, reversed(resulting_versions)):
            assert actual.name == expected["name"]
            assert actual.hash == expected["hash"]


@pytest.mark.asyncio
async def test_update_endpoint_requires_auth(client_unauth: "TestClient"):
    response = await client_unauth.post("/__update")
    assert response.status == 403


@pytest.mark.asyncio
async def test_update_endpoint(
    client_auth: "TestClient",
    seed_db: "Database",
):
    response = await client_auth.post(
        "/__update",
        json={
            "id": 1,
            "name": "new-plugin-name",
            "author": "New Author",
            "description": "New description",
            "tags": ["new-tag-1", "tag-2"],
            "versions": [
                {"name": "30.0.0", "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
                {"name": "32.0.0", "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
            ],
        },
    )

    assert response.status == 200

    assert (await response.json()) == {
        "id": 1,
        "name": "new-plugin-name",
        "author": "New Author",
        "description": "New description",
        "tags": ["new-tag-1", "tag-2"],
        "image_url": "hxxp://fake.domain/artifact_images/new-plugin-name.png",
        "versions": [
            {"name": "30.0.0", "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            {"name": "32.0.0", "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
        ],
    }

    session = seed_db.maker()
    plugin = await seed_db.get_plugin_by_id(session, 1)

    assert plugin.name == "new-plugin-name"
    assert plugin.author == "New Author"
    assert plugin.description == "New description"
    assert len(plugin.tags) == 2
    assert plugin.tags[0].tag == "new-tag-1"
    assert plugin.tags[1].tag == "tag-2"
    assert len(plugin.versions) == 2
    for actual, expected in zip(
        plugin.versions,
        reversed(
            [
                {"name": "30.0.0", "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
                {"name": "32.0.0", "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
            ],
        ),
    ):
        assert actual.name == expected["name"]
        assert actual.hash == expected["hash"]


@pytest.mark.asyncio
async def test_delete_endpoint_requires_auth(client_unauth: "TestClient"):
    response = await client_unauth.post("/__delete")
    assert response.status == 403


@pytest.mark.asyncio
async def test_delete_endpoint(
    client_auth: "TestClient",
    seed_db: "Database",
):
    response = await client_auth.post("/__delete", json={"id": 1})

    assert response.status == 204

    session = seed_db.maker()
    plugin = await seed_db.get_plugin_by_id(session, 1)

    assert plugin is None
