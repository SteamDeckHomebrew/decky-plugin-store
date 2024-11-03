from os import getenv

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from limits import parse, storage, strategies

rate_limit_storage = storage.RedisStorage("redis://redis_db:6379")
increment_limit_per_plugin = parse("2/day")
rate_limit = strategies.FixedWindowRateLimiter(rate_limit_storage)


async def auth_token(authorization: str = Depends(APIKeyHeader(name="Authorization"))) -> None:
    if authorization != getenv("SUBMIT_AUTH_KEY"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INVALID AUTH KEY")
