from typing import TYPE_CHECKING

import pytest
from pytest_lazy_fixtures import lf

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize("client", [lf("client_unauth"), lf("client_auth")])
async def test_index_endpoint(client: "AsyncClient", index_template: str):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.text == index_template


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("client", "return_code"),
    [(lf("client_unauth"), 403), (lf("client_auth"), 200)],
)
async def test_auth_endpoint(client: "AsyncClient", return_code: int):
    response = await client.post("/__auth")
    assert response.status_code == return_code
