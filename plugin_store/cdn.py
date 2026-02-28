from asyncio import sleep
from base64 import b64encode
from hashlib import sha1, sha256
from logging import getLogger
from os import getenv
from typing import TYPE_CHECKING
from urllib.parse import quote

from aiohttp import ClientSession

from constants import CDN_ERROR_RETRY_TIMES

if TYPE_CHECKING:
    from fastapi import UploadFile


IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/avif": ".avif",
}


class B2UploadError(Exception):
    pass


def construct_image_path(plugin_name: str, file_hash: str, mime_type: str) -> str:
    return f"artifact_images/{quote(plugin_name)}-{file_hash}{IMAGE_TYPES[mime_type]}"


async def _b2_get_upload_url():
    async with ClientSession(raise_for_status=True) as web:
        auth_str = f"{getenv('B2_APP_KEY_ID')}:{getenv('B2_APP_KEY')}".encode("utf-8")
        async with web.get(
            "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
            headers={"Authorization": f"Basic {b64encode(auth_str).decode('utf-8')}"},
        ) as auth_res:
            if not auth_res.status == 200:
                raise B2UploadError(f"B2 LOGIN ERROR {await auth_res.read()!r}")
            auth_res_data = await auth_res.json()
            retry_count = 0
            while True:
                async with web.get(
                    f"{auth_res_data['apiUrl']}/b2api/v2/b2_get_upload_url",
                    json={"bucketId": getenv("B2_BUCKET_ID")},
                    headers={"Authorization": auth_res_data["authorizationToken"]},
                ) as res_data:
                    if res_data.status % 100 == 5:
                        retry_count += 1
                        if retry_count == CDN_ERROR_RETRY_TIMES + 1:
                            raise B2UploadError(f"Failed {retry_count} times getting upload URL.")
                        await sleep(retry_count * 5)
                        continue
                    if not res_data.status == 200:
                        res_data.raise_for_status()
                        raise B2UploadError("B2 GET_UPLOAD_URL ERROR ", await res_data.read())
                    res_data = await res_data.json()
                    return (web, res_data["uploadUrl"], res_data["authorizationToken"])


async def _b2_upload(filename: str, binary: "bytes", mime_type: str = "b2/x-auto"):
    result = await _b2_get_upload_url()
    if result is None:
        raise B2UploadError()
    web, uploadUrl, authToken = result
    res_data = await web.post(
        uploadUrl,
        data=binary,
        headers={
            "Authorization": authToken,
            "Content-Type": mime_type,
            "Content-Length": str(len(binary)),
            "X-Bz-Content-Sha1": sha1(binary).hexdigest(),
            "X-Bz-File-Name": filename,
        },
    )
    t = await res_data.text()
    if res_data.status == 200:
        return t
    raise B2UploadError(t)


async def b2_upload(filename: str, binary: "bytes", mime_type: str = "b2/x-auto"):
    attempt = 1
    while True:
        try:
            return await _b2_upload(filename, binary, mime_type)
        except B2UploadError as e:
            getLogger().error(
                f"B2 Upload Failed: {e}. Retrying in {attempt * 5} seconds (Attempt: {attempt}/{CDN_ERROR_RETRY_TIMES})"
            )
            await sleep(attempt * 5)
            attempt += 1
            if attempt == CDN_ERROR_RETRY_TIMES + 1:
                getLogger().error(f"Retried upload {CDN_ERROR_RETRY_TIMES} times. Aborting...")
                return


async def fetch_image(image_url: str) -> "tuple[bytes, str] | None":
    async with ClientSession() as web:
        async with web.get(image_url) as res:
            if res.status == 200 and (mime_type := res.headers.get("Content-Type")) in IMAGE_TYPES:
                return await res.read(), mime_type
    return None


async def upload_image(plugin_name: str, image_url: str) -> "str | None":
    fetched = await fetch_image(image_url)
    if fetched is not None:
        binary, mime_type = fetched
        file_hash = sha256(binary).hexdigest()
        file_path = construct_image_path(plugin_name, file_hash, mime_type)
        await b2_upload(file_path, binary)
        return file_path
    return None
