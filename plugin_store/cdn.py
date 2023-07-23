from base64 import b64encode
from hashlib import sha1, sha256
from os import getenv
from typing import TYPE_CHECKING
from urllib.parse import quote

from aiohttp import ClientSession

if TYPE_CHECKING:
    from fastapi import UploadFile


IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/avif": ".avif",
}


def construct_image_path(plugin_name: str, file_hash: str, mime_type: str) -> str:
    return f"artifact_images/{quote(plugin_name)}-{file_hash}{IMAGE_TYPES[mime_type]}"


async def b2_upload(filename: str, binary: "bytes", mime_type: str = "b2/x-auto"):
    async with ClientSession(raise_for_status=True) as web:
        auth_str = f"{getenv('B2_APP_KEY_ID')}:{getenv('B2_APP_KEY')}".encode("utf-8")
        async with web.get(
            "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
            headers={"Authorization": f"Basic: {b64encode(auth_str).decode('utf-8')}"},
        ) as res:
            if not res.status == 200:
                return print("B2 LOGIN ERROR ", await res.read())
            res_data = await res.json()

            async with web.post(
                f"{res_data['apiUrl']}/b2api/v2/b2_get_upload_url",
                json={"bucketId": getenv("B2_BUCKET_ID")},
                headers={"Authorization": res_data["authorizationToken"]},
            ) as res_data:
                if not res_data.status == 200:
                    res_data.raise_for_status()
                    return print("B2 GET_UPLOAD_URL ERROR ", await res_data.read())
                res_data = await res_data.json()

                res_data = await web.post(
                    res_data["uploadUrl"],
                    data=binary,
                    headers={
                        "Authorization": res_data["authorizationToken"],
                        "Content-Type": mime_type,
                        "Content-Length": str(len(binary)),
                        "X-Bz-Content-Sha1": sha1(binary).hexdigest(),
                        "X-Bz-File-Name": filename,
                    },
                )
                return await res_data.text()


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


async def upload_version(file: "UploadFile"):
    binary = await file.read()
    file_hash = sha256(binary).hexdigest()
    await b2_upload(f"versions/{file_hash}.zip", binary)
    return {
        "hash": file_hash,
    }
