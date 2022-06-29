import os
import re
from pathlib import Path

from naff import Client, MISSING, PrefixedContext, InteractionContext, ComponentContext, Context, listen, DMChannel
from naff.api.events import MessageCreate
from naff.client.errors import HTTPException, CommandOnCooldown, CommandCheckFailure

from secrets import DEBUG, DEBUG_GUILD
from .copypastas import *
from .log import get_logger

__all__ = ("Megumin",)


class Megumin(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(__name__)
        self.default_prefix = "megu "
        self.pre_run_callback = self._prerun
        self.debug_scope = DEBUG_GUILD if DEBUG else MISSING
        self.logger.debug(f"Debug mod is {DEBUG}; This is not a warning just a reminder.")

    async def _prerun(self, ctx: Context, *args, **kwargs) -> None:
        name = ctx.invoke_target
        if isinstance(ctx, ComponentContext):
            return self.logger.debug(f"Running component with id: `{ctx.custom_id}`")

        if isinstance(ctx, InteractionContext):
            args = " ".join(f"{k}:{v}" for k, v in kwargs.items())
        elif isinstance(ctx, PrefixedContext):
            args = " ".join(args)
        self.logger.debug(f"Running command `{name}` with args: `{args or 'None'}`")

    def start(self, token) -> None:
        cogs = [
            cog[:-3]
            for cog in os.listdir(f"{Path(__file__).parent.parent}/cogs")
            if cog not in ("__init__.py",) and cog[-3:] == ".py"
        ]

        if len(cogs) > 0:
            self.logger.info(f"Loading {len(cogs)} cogs: {', '.join(cogs)}")
            for cog in cogs:
                try:
                    self.load_extension(f"cogs.{cog}")
                except Exception:
                    self.logger.error(f"Could not load a cog: {cog}", exc_info=DEBUG)
        super().start(token)

    async def on_error(self, source: str, error: Exception, *args, **kwargs) -> None:
        if isinstance(error, HTTPException):
            errors = error.search_for_message(error.errors)
            out = f"HTTPException: {error.status}|{error.response.reason}: " + "\n".join(errors)
            self.logger.error(out, exc_info=error)
        else:
            self.logger.error(f"Ignoring exception in {source}", exc_info=error)

    async def on_command_error(self, ctx: Context, error: Exception, *args: list, **kwargs: dict) -> None:
        name = ctx.invoke_target
        self.logger.debug(f"Handling error in {name}: {error}")
        if isinstance(error, CommandOnCooldown):
            return await ctx.send(
                f"Baka! That command is on cooldown! Try again in {round(error.cooldown.get_cooldown_time())}"
                f"\n\n**Command Name**: {ctx.command.name}\n"
                f"**Cooldown Time**: {int(error.cooldown.get_cooldown_time())} seconds", ephemeral=True)
        if isinstance(error, CommandCheckFailure):
            return await ctx.send("Looks like you can't do that dummy", ephemeral=True)

    @listen()
    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user}")
        self.logger.info(f"Connected to {len(self.guilds)} guild(s)")
        self.logger.info(f"Add Me: https://discord.com/api/oauth2/authorize?client_id={self.user.id}"
                         f"&permissions=8&scope=bot%20applications.commands")

    @listen()
    async def on_message_create(self, event: MessageCreate):
        if not event.message.author.bot and not isinstance(event.message.channel, DMChannel):
            if re.match(r"\bpancakes?\b|\bdude\b", event.message.content, re.IGNORECASE):
                return await event.message.reply(PANCAKES)
            if re.match(r"\bcunny\b", event.message.content, re.IGNORECASE):
                return await event.message.reply(CUNNY)
            if re.match(r"\bmesugaki\b|\b:anger:\b", event.message.content, re.IGNORECASE):
                return await event.message.reply(MEGUSAKI)
            if re.match(r"\bpumpkin\b", event.message.content, re.IGNORECASE):
                return await event.message.reply(PUMPKIN)
