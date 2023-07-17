from typing import Any, no_type_check

import anyio
import tomlkit
from httpx import AsyncClient, Headers
from interactions import (
    Buckets,
    Extension,
    GuildText,
    InteractionContext,
    IntervalTrigger,
    Message,
    OptionType,
    Permissions,
    Task,
    check,
    cooldown,
    guild_only,
    listen,
    slash_command,
    slash_option,
)
from lxml import etree

from necoarc import Necoarc, has_permission

ID_FILE = anyio.Path(__file__).parent / "last_id.toml"
URL = "https://tweet.whateveritworks.org/glitchy_sus/rss"
HEADERS = Headers({"User-Agent": "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0"})
NITTER = "tweet.whateveritworks.org"
TWITFIX = "vxtwitter.com"


class Cnuy(Extension):
    """Post cunny that @glitchy_sus rewteets."""

    bot: Necoarc

    async def get_cnuy_channel(self, guild_id: int) -> int | None:
        """Function to get the cunny channel for given guild."""
        async with self.bot.db as db:
            guild = await db.server.find_unique(where={"id": guild_id})
            if not guild:
                await db.server.create({"id": guild_id})
                return None
            return guild.cnuy_channel

    async def get_twitter_links(self, xml: etree._Element, last_id: Any) -> list[str]:  # noqa[ANN401]
        """Function to fetch nitter links."""
        links: list[str] = []

        for i in await anyio.to_thread.run_sync(xml.findall, "channel/item"):
            link = await anyio.to_thread.run_sync(i.find, "link")
            if "RT by" in i.find("title").text:  # type: ignore[union-attr,operator]
                new_link = link.text.replace(NITTER, TWITFIX).strip("#m")  # type: ignore[union-attr]
                if new_link.split("/")[-1] == last_id:
                    return links
                links.append(new_link)
        return links

    @Task.create(IntervalTrigger(minutes=30))
    async def check_twitter(self) -> None:
        """Task to check if @glitchy_sus retweeted."""
        if not await ID_FILE.exists():
            base_toml = await anyio.to_thread.run_sync(tomlkit.dumps, {"id": "0"})
            await ID_FILE.write_text(base_toml)

        async with AsyncClient(headers=HEADERS) as c:
            self.bot.logger.debug("🐦 Checking Glitchy's twitter")
            toml = await anyio.to_thread.run_sync(tomlkit.parse, await ID_FILE.read_text())
            data = await c.get(URL)
            xml = await anyio.to_thread.run_sync(etree.fromstring, data.content)

            last_id = toml["id"]
            new_id = await anyio.to_thread.run_sync(xml.find, "channel/item/link")
            new_last_id = new_id.text.split("/")[-1].strip("#m")  # type: ignore[union-attr]

            toml["id"] = new_last_id
            new_toml = await anyio.to_thread.run_sync(tomlkit.dumps, toml)
            await ID_FILE.write_text(new_toml)
            links = await self.get_twitter_links(xml, last_id)

            if links:
                message = "😭 Glitchy just retweeted cunny! 😭\n"
                message += "\n".join(links)

                for g in self.bot.guilds:
                    channel_id = await self.get_cnuy_channel(g.id)

                    if channel_id:
                        self.bot.logger.debug("📩 Sending cunny to server")
                        await self.bot.get_channel(channel_id).send(message)  # type:ignore[union-attr]

    @listen()
    async def on_startup(self) -> None:
        """Even triggered on startup."""
        self.check_twitter.start()

    @slash_command("set_cnuy_channel", description="Set the cunny posting channel for the server")
    @slash_option("channel", description="Name of the channel to set", opt_type=OptionType.CHANNEL, required=True)
    @check(guild_only())
    @check(has_permission(Permissions.MANAGE_CHANNELS))
    @no_type_check
    async def command_set_cnuy_channel(self, ctx: InteractionContext, channel: GuildText) -> Message:
        """Set a cunny channel."""
        if not isinstance(channel, GuildText):
            return await ctx.send("💥 Error! Only guild text channels allowed.", ephemeral=True)

        async with self.bot.db as db:
            await db.server.upsert(
                where={"id": ctx.guild.id},
                data={
                    "create": {"id": ctx.guild.id, "confess_channel": channel.id},
                    "update": {"confess_channel": channel.id},
                },
            )
            self.bot.logger.debug(f"Successfully set confession channel for {ctx.guild.id}")

        return await ctx.send(f"😭 Successfully set {channel.name} as the cunny channel.", ephemeral=True)

    @slash_command("remove_cnuy_channel", description="Remove the cunny posting channel")
    @check(guild_only())
    @check(has_permission(Permissions.MANAGE_CHANNELS))
    @no_type_check
    async def command_remove_cnuy_channel(self, ctx: InteractionContext) -> Message:
        """Remove the cunny channel."""
        async with self.bot.db as db:
            guild = await db.server.find_unique(where={"id": ctx.guild.id})
            if not guild:
                return await ctx.send("💥 Theres no cnuy channel for this server.", ephemeral=True)
            await db.server.update(data={"cnuy_channel": 0}, where={"id": ctx.guild.id})
        return await ctx.send("✅ Successfully removed cnuy channel.", ephemeral=True)

    @slash_command("check_twitter", description="Manually check glitchy's twitter")
    @check(guild_only())
    @cooldown(Buckets.GUILD, 1, 3600)
    @no_type_check
    async def command_manual_twitter(self, ctx: InteractionContext) -> None:
        """Manually check glitchy's twitter."""
        await ctx.send("🐦 Checking twitter...", ephemeral=True)
        await self.check_twitter()
        self.check_twitter.restart()
        await ctx.send("✅ Done checking!", ephemeral=True)
