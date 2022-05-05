from os import getenv, path
from discord.ext.commands import Bot
from discord import Embed
from discord import utils
from aiohttp.web import Application, get, json_response, static, Response, run_app
from aiohttp import ClientSession
from database import Database
from plugin_parser import get_publish_json
from database import Plugin
from asyncio import get_event_loop
from base64 import b64encode
from hashlib import sha1

ADMINS = ["317602018866888705", "181738643008782346"]

async def upload_image(artifact, binary):
    async with ClientSession() as web:
        auth_str = f"{getenv('B2_APP_KEY_ID')}:{getenv('B2_APP_KEY')}".encode("utf-8")
        async with web.get("https://api.backblazeb2.com/b2api/v2/b2_authorize_account", headers={
            "Authorization": f"Basic: {b64encode(auth_str).decode('utf-8')}"
        }) as res:
            if not res.status == 200:
                return print("B2 LOGIN ERROR ", await res.read())
            res = await res.json()
                            
            async with web.post(
                f"{res['apiUrl']}/b2api/v2/b2_get_upload_url",
                json={"bucketId": getenv("B2_BUCKET_ID")},
                headers={"Authorization": res['authorizationToken']}
            ) as res:
                if not res.status == 200:
                    return print("B2 GET_UPLOAD_URL ERROR ", await res.read()) 
                res = await res.json()

                await web.post(res["uploadUrl"], data=binary,
                headers={
                    "Authorization": res["authorizationToken"],
                    "Content-Type": "b2/x-auto",
                    "Content-Length": str(len(binary)),
                    "X-Bz-Content-Sha1": sha1(binary).hexdigest(),
                    "X-Bz-File-Name": f"artifact_images/{artifact.replace('/', '_')}.png"
                })

class PluginStore:
    def __init__(self) -> None:
        self.loop = get_event_loop()
        self.bot = Bot(command_prefix="$")
        self.server = Application(loop=self.loop)
        self.pending_messages = {}
        self.index_page = open(path.join(path.dirname(__file__), 'templates/plugin_browser.html')).read()

        self.register_commands()
        self.server.add_routes([
            get("/", self.index),
            static("/static", path.join(path.dirname(__file__), 'static')),
            get("/get_plugins", self.get_plugins),
            get("/search", self.search_plugins)
        ])
        self.loop.create_task(self.bot.start(getenv("DISCORD_TOKEN")))

    def run(self):
        async def _(self):
            self.database = await Database()
        self.loop.create_task(_(self))
        run_app(self.server, host="0.0.0.0", port="5566", access_log=None)

    async def index(self, request):
        return Response(text=self.index_page, content_type="text/html")

    async def get_plugins(self, request):
        plugins = await self.database.get_plugins()
        return json_response([i.__dict__() for i in plugins])
    
    async def search_plugins(self, request):
        query = request.query.get("query")
        tags = request.query.get("tags")
        if tags:
            tags = [i.strip() for i in tags.split(",")]
        plugins = await self.database.search(query, tags)
        return json_response([i.__dict__() for i in plugins])

    async def approve(self, artifact, version, author, plugin):
        await self.database.set_pending(artifact, version, 0)
        try:
            await author.send_message("Your plugin {} ({}) has been approved and is now listed on the plugin browser!".format(artifact, version))
        except:
            pass
        embed=Embed(title="{}#{} | {}".format(author.name, author.discriminator, artifact.split("/")[0]), description=plugin.description, color=0x213997)
        embed.set_author(name=artifact.split("/")[-1], 
        icon_url="https://cdn.tzatzikiweeb.moe/file/steam-deck-homebrew/SDHomeBrewwwww.png", url="https://github.com/{}".format(artifact))
        embed.set_thumbnail(url="https://cdn.tzatzikiweeb.moe/file/steam-deck-homebrew/")
        await self.bot.get_channel(int(getenv("ANNOUNCEMENT_CHANNEL"))).send(embed=embed)

    async def reject(self, artifact, version, author):
        await author.send_message("Your plugin {} ({}) has been rejected.".format(artifact, version))
        await self.database.remove_plugin(artifact, version)

    def register_commands(self):
        @self.bot.command()
        async def submit(ctx, artifact, version):
            json, hash = await get_publish_json(artifact, version)
            if not json or not "publish" in json:
                return await ctx.send("Either that artifact does not exist, or it does not have a publish field.")
            if json["publish"]["discord_id"] != str(ctx.author.id):
                return await ctx.send("The Discord ID in publish does not match yours. You can only submit your own plugins!")
            try:
                tags = json["publish"]["tags"]
                try:
                    tags.remove("root")
                except:
                    pass
                if "root" in json["flags"]:
                    tags.append("root")
                plugin = Plugin(
                    artifact, version, 1,
                    f"{ctx.author.name}#{ctx.author.discriminator} | {json['author']}",
                    json["publish"]["description"], tags, hash, str(ctx.author.id)
                )
                if ctx.message.attachments:
                    img = ctx.message.attachments[0]
                    if not "image" in img.content_type or img.height > img.width or not img.filename.endswith("png"):
                        return await ctx.send("Not an image or invalid image (Needs to be landscape) or not PNG.")
                    await self.upload_image(artifact, await img.read())

                await self.database.insert_plugin(plugin)
                msg = await self.bot.get_channel(int(getenv("APPROVAL_CHANNEL"))).send("https://github.com/{}/releases/tag/{}".format(artifact, version))
                await msg.add_reaction("✅")
                await msg.add_reaction("❎")
                self.pending_messages[str(msg.id)] = (artifact, version, ctx.author, plugin)
                return await ctx.send("The artifact {} has be queued for admin approval.".format(artifact))
            except KeyError as e:
                return await ctx.send("Your plugin.json is missing a required field: {}".format(e))

        @self.bot.event
        async def on_reaction_add(reaction, user):
            if str(user.id) not in ADMINS and not await self.database.is_approver(str(user.id)):
                return
            msg = self.pending_messages.pop(str(reaction.message.id), None)
            if not msg:
                return
            if str(reaction.emoji) == "✅":
                await self.approve(*msg)
            elif str(reaction.emoji) == "❎":
                await self.reject(*msg)

        @self.bot.command()
        async def approve(ctx, artifact, version):
            if not str(ctx.author.id) in ADMINS and not await self.database.is_approver(str(ctx.author.id)):
                return
            plugins = await self.database.get_plugins(pending=1)
            for i in plugins:
                if i.artifact == artifact and i.version == version:
                    member = utils.get(ctx.message.guild.members, name=i.name.split("#")[0], discriminator=i.name.split("#")[1])
                    return await self.approve(artifact, version, member, i)

        @self.bot.command()
        async def reject(ctx, artifact, version):
            if not str(ctx.author.id) in ADMINS or not await self.database.is_approver(str(ctx.author.id)):
                return
            plugins = await self.database.get_plugins(pending=1)
            for i in plugins:
                if i.artifact == artifact and i.version == version:
                    member = utils.get(ctx.message.guild.members, name=i.name.split("#")[0], discriminator=i.name.split("#")[1])
                    return await self.reject(artifact, version, member, i)

        @self.bot.command()
        async def add_approver(ctx):
            if not str(ctx.author.id) in ADMINS:
                return
            mention = ctx.message.mentions[0]
            author_id = ctx.author.id
            await self.database.add_approver(mention.id, author_id)
            return await ctx.send("Added {} as approver".format(mention.name))

        @self.bot.command()
        async def remove_approver(ctx):
            if not str(ctx.author.id) in ADMINS:
                return
            mention = ctx.message.mentions[0]
            await self.database.remove_approver(mention.id)
            return await ctx.send("Removed {} as approver".format(mention.name))
            
if __name__ == "__main__":
    PluginStore().run()
