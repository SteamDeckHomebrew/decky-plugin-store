from base64 import b64encode
from hashlib import sha1, sha256
from os import getenv
from typing import TYPE_CHECKING

from aiohttp import ClientSession

from database.models import Artifact

if TYPE_CHECKING:
    from fastapi import UploadFile


async def b2_upload(filename: str, binary: "bytes"):
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
                        "Content-Type": "b2/x-auto",
                        "Content-Length": str(len(binary)),
                        "X-Bz-Content-Sha1": sha1(binary).hexdigest(),
                        "X-Bz-File-Name": filename,
                    },
                )
                return await res_data.text()


async def upload_image(plugin: "Artifact", image_url: "str"):
    async with ClientSession() as web:
        async with web.get(image_url) as res:
            if res.status == 200 and res.headers.get("Content-Type") == "image/png":
                await b2_upload(plugin.image_path, await res.read())


async def upload_version(file: "UploadFile"):
    binary = await file.read()
    file_hash = sha256(binary).hexdigest()
    await b2_upload(f"versions/{file_hash}.zip", binary)
    return {
        "hash": file_hash,
    }
