from os import getenv

from discord_webhook import AsyncDiscordWebhook, DiscordEmbed

import constants


async def post_announcement(plugin):
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
