from typing import TYPE_CHECKING

import pytest
from pytest_lazyfixture import lazy_fixture

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize("client", [lazy_fixture("client_unauth"), lazy_fixture("client_auth")])
async def test_index_endpoint(client: "AsyncClient", index_template: str):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.text == index_template


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("client", "return_code"),
    [(lazy_fixture("client_unauth"), 403), (lazy_fixture("client_auth"), 200)],
)
async def test_auth_endpoint(client: "AsyncClient", return_code: int):
    response = await client.post("/__auth")
    assert response.status_code == return_code
