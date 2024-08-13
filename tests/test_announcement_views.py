from typing import TYPE_CHECKING

import pytest
from fastapi import status
from pytest_lazyfixture import lazy_fixture

if TYPE_CHECKING:
    from freezegun.api import FrozenDateTimeFactory
    from httpx import AsyncClient

    from database.database import Database


@pytest.mark.parametrize(
    ("endpoint", "method"),
    [
        ("/v1/announcements", "GET"),
        ("/v1/announcements", "POST"),
        ("/v1/announcements/01234568-79ab-7cde-a445-b9f117ca645d", "GET"),
        ("/v1/announcements/01234568-79ab-7cde-a445-b9f117ca645d", "PUT"),
        ("/v1/announcements/01234568-79ab-7cde-a445-b9f117ca645d", "DELETE"),
    ],
)
async def test_endpoints_requiring_auth(client_unauth: "AsyncClient", endpoint: str, method: str):
    response = await client_unauth.request(method, endpoint)
    assert response.status_code == 403


@pytest.mark.parametrize("client", [lazy_fixture("client_unauth"), lazy_fixture("client_auth")])
@pytest.mark.parametrize(
    ("origin", "result"),
    [("https://example.com", status.HTTP_400_BAD_REQUEST), ("https://steamloopback.host", status.HTTP_200_OK)],
)
async def test_current_announcement_list_endpoint_cors(
    client: "AsyncClient",
    origin: str,
    result: int,
):
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Example",
    }
    response = await client.options("/v1/announcements/-/current", headers=headers)

    assert response.status_code == result


async def test_announcement_list(
    client_auth: "AsyncClient",
    seed_db: "Database",
):
    response = await client_auth.get("/v1/announcements")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0] == {
        "id": "89abcdef-79ab-7cde-99e0-56b0d2e2dcdb",
        "title": "Test announcement 2",
        "text": "Seriously! Just a drill!",
        "created": "2023-11-16T00:01:00Z",
        "updated": "2023-11-16T00:01:00Z",
    }
    assert data[1] == {
        "id": "01234568-79ab-7cde-a445-b9f117ca645d",
        "title": "Test announcement 1",
        "text": "This is only a drill!",
        "created": "2023-11-16T00:00:00Z",
        "updated": "2023-11-16T00:00:00Z",
    }


async def test_announcement_create(
    client_auth: "AsyncClient",
    seed_db: "Database",
    freezer: "FrozenDateTimeFactory",
    _mock_uuidv7_generation,
):
    freezer.move_to("2023-12-01T00:00:00Z")
    response = await client_auth.post("/v1/announcements", json={"title": "Test 3", "text": "Drill test!"})

    assert response.status_code == 201
    data = response.json()

    assert data["title"] == "Test 3"
    assert data["text"] == "Drill test!"
    assert data == {
        "id": "018c22ac-d000-7444-9111-111111111111",
        "title": "Test 3",
        "text": "Drill test!",
        "created": "2023-12-01T00:00:00Z",
        "updated": "2023-12-01T00:00:00Z",
    }

    response = await client_auth.get("/v1/announcements")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 3


@pytest.mark.parametrize("client", [lazy_fixture("client_unauth"), lazy_fixture("client_auth")])
async def test_announcement_list_current(
    client: "AsyncClient",
    seed_db: "Database",
):
    response = await client.get("/v1/announcements/-/current")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0] == {
        "id": "89abcdef-79ab-7cde-99e0-56b0d2e2dcdb",
        "title": "Test announcement 2",
        "text": "Seriously! Just a drill!",
        "created": "2023-11-16T00:01:00Z",
        "updated": "2023-11-16T00:01:00Z",
    }
    assert data[1] == {
        "id": "01234568-79ab-7cde-a445-b9f117ca645d",
        "title": "Test announcement 1",
        "text": "This is only a drill!",
        "created": "2023-11-16T00:00:00Z",
        "updated": "2023-11-16T00:00:00Z",
    }


async def test_announcement_fetch(
    client_auth: "AsyncClient",
    seed_db: "Database",
):
    response = await client_auth.get("/v1/announcements/01234568-79ab-7cde-a445-b9f117ca645d")

    assert response.status_code == 200
    data = response.json()

    assert data == {
        "id": "01234568-79ab-7cde-a445-b9f117ca645d",
        "title": "Test announcement 1",
        "text": "This is only a drill!",
        "created": "2023-11-16T00:00:00Z",
        "updated": "2023-11-16T00:00:00Z",
    }


async def test_announcement_update(
    client_auth: "AsyncClient",
    seed_db: "Database",
    freezer: "FrozenDateTimeFactory",
):
    freezer.move_to("2023-12-01T00:00:00Z")
    response = await client_auth.put(
        "/v1/announcements/01234568-79ab-7cde-a445-b9f117ca645d",
        json={"title": "First test announcement", "text": "Drilling!"},
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data == {
        "id": "01234568-79ab-7cde-a445-b9f117ca645d",
        "title": "First test announcement",
        "text": "Drilling!",
        "created": "2023-11-16T00:00:00Z",
        "updated": "2023-12-01T00:00:00Z",
    }


async def test_announcement_delete(
    client_auth: "AsyncClient",
    seed_db: "Database",
    freezer: "FrozenDateTimeFactory",
):
    freezer.move_to("2023-12-01T00:00:00Z")
    response = await client_auth.delete("/v1/announcements/01234568-79ab-7cde-a445-b9f117ca645d")

    assert response.status_code == 204, response.text

    response = await client_auth.get("/v1/announcements")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] != "01234568-79ab-7cde-a445-b9f117ca645d"
