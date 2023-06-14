from os import getenv
from typing import TYPE_CHECKING

from discord_webhook import AsyncDiscordWebhook, DiscordEmbed

import constants

if TYPE_CHECKING:
    from database.models import Artifact, Version


async def post_announcement(plugin: "Artifact", version: "Version"):
    webhook = AsyncDiscordWebhook(url=getenv("ANNOUNCEMENT_WEBHOOK"))
    embed = DiscordEmbed(title=plugin.name, description=plugin.description, color=0x213997)

    embed.set_author(
        name=plugin.author,
        icon_url=f"{constants.CDN_URL}SDHomeBrewwwww.png",
    )
    embed.set_thumbnail(url=plugin.image_url)
    embed.set_footer(text=f"Version {version.name}")

    webhook.add_embed(embed)
    await webhook.execute()
