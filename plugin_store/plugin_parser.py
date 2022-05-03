from zipfile import ZipFile
from aiohttp import ClientSession
from io import BytesIO
from asyncio import get_event_loop
from concurrent.futures import ProcessPoolExecutor
from json import load
from hashlib import sha256

def _get_publish_json(zip):
    zip_file = ZipFile(zip)
    plugin_json = None
    for file in zip_file.namelist():
        if "plugin.json" in file:
            plugin_json = file
            break
    if not plugin_json:
        return None
    return (load(zip_file.open(plugin_json)), sha256(zip.getbuffer()).hexdigest())

async def get_publish_json(artifact, version):
    async with ClientSession() as client:
        url = "https://github.com/{}/archive/refs/tags/{}.zip".format(artifact, version)
        res = await client.get(url)
        if res.status == 200:
            data = await res.read()
            res_zip = BytesIO(data)
            with ProcessPoolExecutor() as executor:
                return await get_event_loop().run_in_executor(
                    executor,
                    _get_publish_json,
                    res_zip
                )