from asyncio import create_task
from base64 import b64encode
from hashlib import sha1, sha256
from os import getenv, path
from typing import TYPE_CHECKING

import aiohttp_cors
from aiohttp import ClientSession
from aiohttp.web import Application, get, json_response, post, Response, run_app
from discord_webhook import AsyncDiscordWebhook, DiscordEmbed
from sqlalchemy.ext.asyncio import AsyncSession

import constants
from database.database import Database

if TYPE_CHECKING:
    from typing import Mapping

    from database.models import Artifact


async def b2_upload(filename, binary):
    async with ClientSession() as web:
        auth_str = f"{getenv('B2_APP_KEY_ID')}:{getenv('B2_APP_KEY')}".encode("utf-8")
        async with web.get(
            "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
            headers={"Authorization": f"Basic: {b64encode(auth_str).decode('utf-8')}"},
        ) as res:
            if not res.status == 200:
                return print("B2 LOGIN ERROR ", await res.read())
            res = await res.json()

            async with web.post(
                f"{res['apiUrl']}/b2api/v2/b2_get_upload_url",
                json={"bucketId": getenv("B2_BUCKET_ID")},
                headers={"Authorization": res["authorizationToken"]},
            ) as res:
                if not res.status == 200:
                    return print("B2 GET_UPLOAD_URL ERROR ", await res.read())
                res = await res.json()

                res = await web.post(
                    res["uploadUrl"],
                    data=binary,
                    headers={
                        "Authorization": res["authorizationToken"],
                        "Content-Type": "b2/x-auto",
                        "Content-Length": str(len(binary)),
                        "X-Bz-Content-Sha1": sha1(binary).hexdigest(),
                        "X-Bz-File-Name": filename,
                    },
                )
                return await res.text()


class PluginStore:
    def __init__(self) -> None:
        self.server = Application()
        self.database = Database(getenv("DB_PATH"))
        self.index_page = open(path.join(path.dirname(__file__), "templates/plugin_browser.html")).read()

        self.server.add_routes(
            [
                get("/", self.index),
                get("/plugins", self.plugins),
                post("/__submit", self.submit_plugin),
                post("/__delete", self.delete_plugin),
                post("/__update", self.update_plugin),
                post("/__auth", self.check_auth),
            ],
        )
        self.cors = aiohttp_cors.setup(
            self.server,
            defaults={
                "https://steamloopback.host": aiohttp_cors.ResourceOptions(expose_headers="*", allow_headers="*"),
            },
        )
        for route in list(self.server.router.routes()):
            self.cors.add(route)

    async def make_app(self):
        create_task(self.database.init())
        return self.server

    def run(self):
        run_app(self.make_app(), host="0.0.0.0", port=5566, access_log=None)

    async def index(self, _):
        return Response(text=self.index_page, content_type="text/html")

    async def plugins(self, request):
        query = request.query.get("query")
        tags = request.query.get("tags")
        include_hidden = self.get_boolean(request.query, "hidden", False)
        if tags:
            tags = [i.strip() for i in tags.split(",")]
        session = self.database.maker()
        try:
            plugins = await self.database.search(session, query, tags, include_hidden)
            return json_response([i.to_dict(with_visibility=include_hidden) for i in plugins])
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def check_auth(self, request):
        if request.headers.get("Authorization") != getenv("SUBMIT_AUTH_KEY"):
            return Response(status=403, text="INVALID AUTH KEY")
        return Response(status=200, text="Success")

    async def delete_plugin(self, request):
        if request.headers.get("Authorization") != getenv("SUBMIT_AUTH_KEY"):
            return Response(status=403, text="INVALID AUTH KEY")
        data = await request.json()
        id = data["id"]
        session = self.database.maker()
        try:
            await self.database.delete_plugin(session, id)
            return Response(status=204, text="Deleted")
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def update_plugin(self, request):
        if request.headers.get("Authorization") != getenv("SUBMIT_AUTH_KEY"):
            return Response(status=403, text="INVALID AUTH KEY")
        data = await request.json()
        plugin_id = data["id"]
        author = data["author"]
        description = data["description"]
        name = data["name"]
        tags = data["tags"]
        versions = data["versions"]
        visible = self.get_boolean(data, "visible", True)
        session: AsyncSession = self.database.maker()
        try:
            await self.database.delete_plugin(session, plugin_id)
            new_plugin = await self.database.insert_artifact(
                session=session,
                id=plugin_id,
                name=name,
                author=author,
                description=description,
                tags=tags,
                visible=visible,
            )
            for version in reversed(versions):
                await self.database.insert_version(session, new_plugin.id, **version)
            await session.refresh(new_plugin)
            return json_response(new_plugin.to_dict(with_visibility=True), status=200)
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def submit_plugin(self, request):
        if request.headers.get("Authorization") != getenv("SUBMIT_AUTH_KEY"):
            return Response(status=403, text="INVALID AUTH KEY")
        data = await request.post()

        name = data["name"]
        author = data["author"]
        description = data["description"]
        tags = [i.strip() for i in data["tags"].split(",")]

        version_name = data["version_name"]
        image_url = data["image"]
        file_bin = data["file"].file.read()
        force = False

        if "force" in data and data["force"]:
            force = data["force"].strip().title() in ["True", "1"]

        session = self.database.maker()
        try:
            artifact = await self.database.get_plugin_by_name(session, name)

            if artifact and force:
                await self.database.delete_plugin(session, artifact.id)
                artifact = None

            if artifact is not None:
                artifact: "Artifact"
                if version_name in [i.name for i in artifact.versions]:
                    return json_response({"message": "Version already exists"}, status=400)
                artifact = await self.database.update_artifact(
                    session,
                    artifact,
                    author=author,
                    description=description,
                    tags=tags,
                )

            else:
                artifact = await self.database.insert_artifact(
                    session=session,
                    name=name,
                    author=author,
                    description=description,
                    tags=tags,
                )

            ver = await self.database.insert_version(
                session,
                artifact.id,
                name=version_name,
                hash=sha256(file_bin).hexdigest(),
            )

            await session.refresh(artifact)
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

        await b2_upload(f"versions/{ver.hash}.zip", file_bin)
        await self.upload_image(artifact, image_url)
        await self.post_announcement(artifact)
        return json_response(artifact.to_dict(), status=201)

    async def upload_image(self, plugin, image_url):
        async with ClientSession() as web:
            async with web.get(image_url) as res:
                if res.status == 200 and res.headers.get("Content-Type") == "image/png":
                    await b2_upload(plugin.image_path, await res.read())

    async def post_announcement(self, plugin):
        webhook = AsyncDiscordWebhook(url=getenv("ANNOUNCEMENT_WEBHOOK"))
        embed = DiscordEmbed(title=plugin.name, description=plugin.description, color=0x213997)

        embed.set_author(
            name=plugin.author,
            icon_url=f"{constants.CDN_URL}SDHomeBrewwwww.png",
            url=f"https://github.com/{plugin.author}/{plugin.name}",
        )
        embed.set_thumbnail(url=plugin.image_url)
        embed.set_footer(text=f"Version {plugin.versions[-1].name}")

        webhook.add_embed(embed)
        await webhook.execute()

    @classmethod
    def get_boolean(cls, data: "Mapping", field: "str", default: "bool") -> "bool":
        value = data.get(field, default)
        if isinstance(value, str):
            value = value.lower()
            return value in {"t", "true", "1"}

        return bool(value)


if __name__ == "__main__":
    PluginStore().run()
