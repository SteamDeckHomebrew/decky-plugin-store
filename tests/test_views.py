from typing import TYPE_CHECKING
from urllib.parse import urlencode

import pytest
from fastapi import status
from pytest_lazyfixture import lazy_fixture
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound

from database.models.Artifact import Tag

if TYPE_CHECKING:
    from typing import Union

    from httpx import AsyncClient

    from database.database import Database


@pytest.mark.asyncio
@pytest.mark.parametrize("client", [lazy_fixture("client_unauth"), lazy_fixture("client_auth")])
async def test_index_endpoint(client: "AsyncClient", index_template: str):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.text == index_template


@pytest.mark.asyncio
@pytest.mark.parametrize("client", [lazy_fixture("client_unauth"), lazy_fixture("client_auth")])
@pytest.mark.parametrize(
    ("origin", "result"),
    [("https://example.com", status.HTTP_400_BAD_REQUEST), ("https://steamloopback.host", status.HTTP_200_OK)],
)
async def test_plugin_list_endpoint_cors(
    client: "AsyncClient",
    origin: str,
    result: int,
):
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Example",
    }
    response = await client.options("/plugins", headers=headers)

    assert response.status_code == result


@pytest.mark.asyncio
@pytest.mark.parametrize("client", [lazy_fixture("client_unauth"), lazy_fixture("client_auth")])
@pytest.mark.parametrize(
    ("query_filter", "query_plugin_ids"),
    [
        pytest.param(None, {1, 2, 3, 4, 5, 6, 7, 8}, id="no-query"),
        pytest.param("plugin-", {1, 2, 4, 5, 6, 8}, id="query-plugin-"),
        pytest.param("", {1, 2, 3, 4, 5, 6, 7, 8}, id="query-empty"),
        pytest.param("third", {3}, id="query-third"),
    ],
)
@pytest.mark.parametrize(
    ("tags_filter", "tag_plugin_ids"),
    [
        pytest.param(None, {1, 2, 3, 4, 5, 6, 7, 8}, id="no-tags"),
        pytest.param("tag-2", {1, 3, 5, 7}, id="tags-tag-2"),
        pytest.param("", {1, 2, 3, 4, 5, 6, 7, 8}, id="tags-empty"),
        pytest.param("tag-1,tag-3", {2, 6}, id="tags-tag-1-tag-3"),
    ],
)
@pytest.mark.parametrize(
    ("hidden_filter", "hidden_plugin_ids", "show_visibility"),
    [
        pytest.param(None, {1, 2, 3, 4}, False, id="no-hidden"),
        pytest.param("0", {1, 2, 3, 4}, False, id="hidden-0"),
        pytest.param("false", {1, 2, 3, 4}, False, id="hidden-false"),
        pytest.param("False", {1, 2, 3, 4}, False, id="hidden-False"),
        pytest.param("f", {1, 2, 3, 4}, False, id="hidden=f"),
        pytest.param("1", {1, 2, 3, 4, 5, 6, 7, 8}, True, id="hidden-1"),
        pytest.param("true", {1, 2, 3, 4, 5, 6, 7, 8}, True, id="hidden-true"),
        pytest.param("True", {1, 2, 3, 4, 5, 6, 7, 8}, True, id="hidden-True"),
        pytest.param("t", {1, 2, 3, 4, 5, 6, 7, 8}, True, id="hidden-t"),
    ],
)
async def test_plugins_list_endpoint(
    seed_db: "Database",
    client: "AsyncClient",
    query_filter: "str | None",
    query_plugin_ids: set[int],
    tags_filter: "str | None",
    tag_plugin_ids: set[int],
    hidden_filter: "str | bool | None",
    hidden_plugin_ids: set[int],
    show_visibility: bool,
):
    plugin_ids = query_plugin_ids & tag_plugin_ids & hidden_plugin_ids
    params: "dict[str, Union[str | bool]]" = {}
    if query_filter is not None:
        params["query"] = query_filter
    if tags_filter is not None:
        params["tags"] = tags_filter
    if hidden_filter is not None:
        params["hidden"] = hidden_filter
    response = await client.get(f"/plugins?{urlencode(params)}")
    expected_response = [
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
            **({"visible": True} if show_visibility else {}),
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
            **({"visible": True} if show_visibility else {}),
        },
        {
            "id": 3,
            "name": "third",
            "author": "author-of-third",
            "description": "Description of third",
            "tags": ["tag-2", "tag-3"],
            "image_url": "hxxp://fake.domain/artifact_images/third.png",
            "versions": [
                {"name": "3.2.0", "hash": "ec2516b144cb429b1473104efcbe345da2b82347fbbb587193a22429a0dc6ab6"},
                {"name": "3.1.0", "hash": "8d9a561a9fc5c7509b5fe0e54213641e502e3b1e456af34cc44aa0a526f85f9b"},
                {"name": "3.0.0", "hash": "9463611d748129d063f697ec7bdd770b7d5b82c50b93582e31e6440236ba8f66"},
            ],
            **({"visible": True} if show_visibility else {}),
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
            **({"visible": True} if show_visibility else {}),
        },
        {
            "id": 5,
            "name": "plugin-5",
            "author": "author-of-plugin-5",
            "description": "Description of plugin-5",
            "tags": ["tag-1", "tag-2"],
            "image_url": "hxxp://fake.domain/artifact_images/plugin-5.png",
            "versions": [
                {"name": "1.0.0", "hash": "562eec14bf4b01c5769acb1b8854b3382b7bbc7333f45d2fd200a752f72fa3a0"},
                {"name": "0.2.0", "hash": "37014c0eca288692ff8992ce1ef0d590a76c3eb1c44f7d9dc1e6963221ec87f8"},
                {"name": "0.1.0", "hash": "6c5e8ab31c430eaed0d9876ea164769913e64094848ca8bfd44d322a769e49cd"},
            ],
            **({"visible": False} if show_visibility else {}),
        },
        {
            "id": 6,
            "name": "plugin-6",
            "author": "author-of-plugin-6",
            "description": "Description of plugin-6",
            "tags": ["tag-1", "tag-3"],
            "image_url": "hxxp://fake.domain/artifact_images/plugin-6.png",
            "versions": [
                {"name": "2.0.0", "hash": "611a4f133a0e2f7ca4285478d4be7c6e09acc256c9f47d71a075d2af279d2c96"},
                {"name": "1.1.0", "hash": "dd3ea0a0674ac176f431d0dd3ae11df7a56368f1ce8965c6bf41ae264cbb0eb3"},
            ],
            **({"visible": False} if show_visibility else {}),
        },
        {
            "id": 7,
            "name": "seventh",
            "author": "author-of-seventh",
            "description": "Description of seventh",
            "tags": ["tag-2", "tag-3"],
            "image_url": "hxxp://fake.domain/artifact_images/seventh.png",
            "versions": [
                {"name": "3.2.0", "hash": "a4410618d61cf061f508d0c20fb7145bf28ae218eec7154071c3ec03ec04ec5b"},
                {"name": "3.1.0", "hash": "9848a9d18e91da6cd678adccbbdfa09474cc587e96234dfd72c2a1d0f0c8132c"},
                {"name": "3.0.0", "hash": "370e6e290c94ba02af39fc11d67f0e8769e00bcb3b7e21499bc0be622fe676e9"},
            ],
            **({"visible": False} if show_visibility else {}),
        },
        {
            "id": 8,
            "name": "plugin-8",
            "author": "author-of-plugin-8",
            "description": "Description of plugin-8",
            "tags": ["tag-1"],
            "image_url": "hxxp://fake.domain/artifact_images/plugin-8.png",
            "versions": [
                {"name": "4.0.0", "hash": "44bc28702614ff73ae8c68dc6298369bb25e792776925930bd38ea592df36af9"},
                {"name": "3.0.0", "hash": "c9514fc40d9c32dee69033b104102abac98e6689ccfe48d947e30991e1778a88"},
                {"name": "2.0.0", "hash": "6f55affd9be35d799a6d6967bbf6822240f19d22a9cbe340443d5c499a4a75ab"},
                {"name": "1.0.0", "hash": "bae8a710fe1e925b3f1489b7a4e50d6555be40182f238e65736ced607489e3b3"},
            ],
            **({"visible": False} if show_visibility else {}),
        },
    ]
    assert response.status_code == 200
    assert response.json() == [response_obj for response_obj in expected_response if response_obj["id"] in plugin_ids]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("client", "return_code"),
    [(lazy_fixture("client_unauth"), 403), (lazy_fixture("client_auth"), 200)],
)
async def test_auth_endpoint(client: "AsyncClient", return_code: int):
    response = await client.post("/__auth")
    assert response.status_code == return_code


@pytest.mark.asyncio
async def test_submit_endpoint_requires_auth(client_unauth: "AsyncClient"):
    response = await client_unauth.post("/__submit")
    assert response.status_code == 403


@pytest.mark.parametrize(
    ("db_fixture", "plugin_submit_data", "id", "name", "return_code", "resulting_versions", "error_msg", "is_visible"),
    [
        (
            lazy_fixture("db"),
            "new-plugin",
            1,
            "new-plugin",
            status.HTTP_201_CREATED,
            [{"name": "2.0.0", "hash": "378d3213bf3c5d1924891c05659425e7d62bb786665cb2eb5c88564a327b03c7"}],
            None,
            True,
        ),
        (
            lazy_fixture("seed_db"),
            "plugin-1",
            1,
            "plugin-1",
            status.HTTP_201_CREATED,
            [
                {"name": "2.0.0", "hash": "378d3213bf3c5d1924891c05659425e7d62bb786665cb2eb5c88564a327b03c7"},
                {"name": "1.0.0", "hash": "f06b77407d0ef08f5667591ab386eeff2090c340f3eadf76006db6d1ac721029"},
                {"name": "0.2.0", "hash": "750e557099102527b927be4b9e79392c8f4e011d8a5848480afb61fc0de4f5af"},
                {"name": "0.1.0", "hash": "44733735485ece810402fff9e7a608a49039c0b363e52ff62d07b84ab2b40b06"},
            ],
            None,
            True,
        ),
        (
            lazy_fixture("seed_db"),
            "plugin-5",
            5,
            "plugin-5",
            status.HTTP_201_CREATED,
            [
                {"name": "2.0.0", "hash": "378d3213bf3c5d1924891c05659425e7d62bb786665cb2eb5c88564a327b03c7"},
                {"name": "1.0.0", "hash": "562eec14bf4b01c5769acb1b8854b3382b7bbc7333f45d2fd200a752f72fa3a0"},
                {"name": "0.2.0", "hash": "37014c0eca288692ff8992ce1ef0d590a76c3eb1c44f7d9dc1e6963221ec87f8"},
                {"name": "0.1.0", "hash": "6c5e8ab31c430eaed0d9876ea164769913e64094848ca8bfd44d322a769e49cd"},
            ],
            None,
            False,
        ),
        (lazy_fixture("seed_db"), "plugin-2", 1, "plugin-2", 400, [], "Version already exists", True),
    ],
    ids=[
        "creates_new_plugin",
        "uploads_new_version",
        "uploads_new_version_for_hidden",
        "blocks_overriding_existing_version",
    ],
    indirect=["plugin_submit_data"],
)
@pytest.mark.asyncio
async def test_submit_endpoint(
    client_auth: "AsyncClient",
    db_fixture: "Database",
    plugin_submit_data: "tuple[dict, dict]",
    id: int,
    name: str,
    return_code: int,
    resulting_versions: list[dict],
    error_msg: "str | None",
    is_visible: bool,
):
    submit_data, submit_files = plugin_submit_data
    response = await client_auth.post("/__submit", data=submit_data, files=submit_files)
    assert response.status_code == return_code, response.text
    if return_code >= status.HTTP_400_BAD_REQUEST:
        assert response.json()["message"] == error_msg
    else:
        assert response.json() == {
            "id": id,
            "name": name,
            "author": "plugin-author-of-new-plugin",
            "description": "Description of our brand new plugin!",
            "tags": ["new-tag-2", "tag-1"],
            "image_url": f"hxxp://fake.domain/artifact_images/{name}.png",
            "versions": resulting_versions,
        }

        plugin = await db_fixture.get_plugin_by_id(db_fixture.session, id)

        assert plugin is not None

        assert plugin.name == name
        assert plugin.author == "plugin-author-of-new-plugin"
        assert plugin.description == "Description of our brand new plugin!"
        assert len(plugin.tags) == 2
        assert plugin.tags[0].tag == "new-tag-2"
        assert plugin.tags[1].tag == "tag-1"
        assert len(plugin.versions) == len(resulting_versions)
        assert plugin.visible is is_visible
        for actual, expected in zip(plugin.versions, resulting_versions):
            assert actual.name == expected["name"]
            assert actual.hash == expected["hash"]

        statement = select(Tag).where(Tag.tag == "tag-1").with_only_columns([func.count()]).order_by(None)
        assert (await db_fixture.session.execute(statement)).scalar() == 1
        statement = select(Tag).where(Tag.tag == "new-tag-2").with_only_columns([func.count()]).order_by(None)
        assert (await db_fixture.session.execute(statement)).scalar() == 1

        list_response = await client_auth.get("/plugins")
        returned_ids = {plugin["id"] for plugin in list_response.json()}
        if is_visible:
            assert id in returned_ids
        else:
            assert id not in returned_ids


@pytest.mark.asyncio
async def test_update_endpoint_requires_auth(client_unauth: "AsyncClient"):
    response = await client_unauth.post("/__update")
    assert response.status_code == 403


@pytest.mark.parametrize("make_visible", (True, False))
@pytest.mark.parametrize("pick_visible", (True, False))
@pytest.mark.asyncio
async def test_update_endpoint(
    client_auth: "AsyncClient",
    seed_db: "Database",
    pick_visible: bool,
    make_visible: bool,
):
    response = await client_auth.post(
        "/__update",
        json={
            "id": 1 if pick_visible else 5,
            "name": "new-plugin-name",
            "author": "New Author",
            "description": "New description",
            "tags": ["new-tag-1", "tag-2"],
            "versions": [
                {"name": "30.0.0", "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
                {"name": "32.0.0", "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
            ],
            "visible": "true" if make_visible else "false",
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()

    assert (response.json()) == {
        "id": 1 if pick_visible else 5,
        "name": "new-plugin-name",
        "author": "New Author",
        "description": "New description",
        "tags": ["new-tag-1", "tag-2"],
        "image_url": "hxxp://fake.domain/artifact_images/new-plugin-name.png",
        "versions": [
            {"name": "30.0.0", "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            {"name": "32.0.0", "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
        ],
        "visible": make_visible,
    }

    plugin = await seed_db.get_plugin_by_id(seed_db.session, 1 if pick_visible else 5)

    assert plugin is not None

    assert plugin.name == "new-plugin-name"
    assert plugin.author == "New Author"
    assert plugin.description == "New description"
    assert plugin.visible is make_visible
    assert len(plugin.tags) == 2
    assert plugin.tags[0].tag == "new-tag-1"
    assert plugin.tags[1].tag == "tag-2"
    assert len(plugin.versions) == 2
    for actual, expected in zip(
        plugin.versions,
        [
            {"name": "30.0.0", "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            {"name": "32.0.0", "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
        ],
    ):
        assert actual.name == expected["name"]
        assert actual.hash == expected["hash"]

    statement = select(Tag).where(Tag.tag == "new-tag-1").with_only_columns([func.count()]).order_by(None)
    assert (await seed_db.session.execute(statement)).scalar() == 1
    statement = select(Tag).where(Tag.tag == "tag-2").with_only_columns([func.count()]).order_by(None)
    assert (await seed_db.session.execute(statement)).scalar() == 1


@pytest.mark.asyncio
async def test_delete_endpoint_requires_auth(client_unauth: "AsyncClient"):
    response = await client_unauth.post("/__delete")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_delete_endpoint(
    client_auth: "AsyncClient",
    seed_db: "Database",
):
    response = await client_auth.post("/__delete", json={"id": 1})

    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(NoResultFound):
        await seed_db.get_plugin_by_id(seed_db.session, 1)
