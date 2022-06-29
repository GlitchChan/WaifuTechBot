import datetime
from io import BytesIO

from naff import (
    Extension,
    OptionTypes,
    InteractionContext,
    User,
    slash_command,
    slash_option,
    prefixed_command,
    PrefixedContext,
    File,
    Embed,
    Attachment,
    check,
    dm_only,
)
from petpetgif import petpet

import secrets
from core.ext import embed_builder
from core import Megumin, get_logger


def confession_embed(confession: str, image: Attachment = None) -> Embed:
    """
    Create a confession embed for confession command

    :param confession: The confession
    :param image: A discord Attachment if any
    :returns: A discord embed
    """

    emb = await embed_builder(
        title="Anonymous Confession",
        description=confession,
        footer=["Type /confess or DM me \'megu confess `confession`\'"],
        image=image.url if image else None,
        timestamp=datetime.datetime.now()
    )

    return emb


class Memes(Extension):
    def __init__(self, client):
        self.client: Megumin = client
        self.logger = get_logger(__class__.__name__)
        self.logger.info(f"{__class__.__name__} Cog loaded")

    @slash_command("pet_pet", description="Pat a user")
    @slash_option("user", "User you want to pat", OptionTypes.USER, required=True)
    async def pet_pet(self, ctx: InteractionContext, user: User):
        source = BytesIO(await user.avatar.fetch())
        dest = BytesIO()
        petpet.make(source, dest)
        dest.seek(0)

        petpet_file = File(file=dest, file_name="petpet.gif")

        await ctx.send(file=petpet_file)

    @slash_command("confess", description="Anonymous confession")
    @slash_option("confession", "Your confession", OptionTypes.STRING, required=True)
    @slash_option("image", "Any image you want to add", OptionTypes.ATTACHMENT, required=False)
    async def confess(self, ctx: InteractionContext, confession: str, image: Attachment = None):
        emb = confession_embed(confession, image)

        await ctx.send("Sending confession", ephemeral=True)
        await self.client.get_channel(secrets.CONFESSION_CHANNEL).send(embeds=[emb])

    @prefixed_command("confess", usage="megu <confession>")
    @check(dm_only())
    async def prefixed_confess(self, ctx: PrefixedContext, *confession: str):
        """Anonymous confession"""
        attachments = ctx.message.attachments
        emb = confession_embed(" ".join(confession), attachments[0] if attachments else None)

        await ctx.send("Sending confession", delete_after=5)
        await self.client.get_channel(secrets.CONFESSION_CHANNEL).send(embeds=[emb])


def setup(client):
    Memes(client)
