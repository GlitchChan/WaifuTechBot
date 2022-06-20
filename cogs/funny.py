import mimetypes
import random
import uuid
from io import BytesIO

import aiohttp
import asyncprawcore.exceptions
from asyncpraw import Reddit
from asyncpraw.models import Submission
from naff import (
    Extension,
    OptionTypes,
    InteractionContext,
    User,
    Embed,
    Color,
    SlashCommandChoice,
    slash_command,
    slash_option,
    check,
    is_owner, File
)

from config import REDDIT_ID, REDDIT_SECRET
from core import Megumin, get_logger


class Funny(Extension):
    def __init__(self, client: Megumin):
        self.client = client
        self.logger = get_logger(__class__.__name__)
        self.logger.info(f"{__class__.__name__} Cog loaded")

    @slash_command("dm_spam", description="Spams a user with a given message")
    @slash_option("user", "User you want to spam", OptionTypes.USER, required=True)
    @slash_option("message", "The message you want sent", OptionTypes.STRING, required=True)
    @slash_option("repeat", "How many times you want the message repeated", OptionTypes.INTEGER, required=False)
    @check(is_owner())
    async def dm_spam(self, ctx: InteractionContext, user: User, message: str, repeat: int):
        await ctx.defer(ephemeral=True)

        # Edge Case
        if repeat == 0:
            await ctx.send("Repeat has to be greater than 0", ephemeral=True)

        while repeat > 0:
            try:
                await user.send(message)
                repeat -= 1
            except Exception:
                continue

        await ctx.send(f"Done spamming {user.mention} with message: `{message}`", ephemeral=True)

    @slash_command("rate_me", description="I will rate the person you give")
    @slash_option("ratee", "Thing you want to rate", OptionTypes.STRING, required=False)
    async def rate_me(self, ctx: InteractionContext, ratee: str):
        rating = hash(ratee) % 10
        await ctx.send(f"I rate {ratee} a {rating}/10")

    # TODO: Switch from Reddit api to Teddit: https://codeberg.org/teddit/teddit/wiki#teddit-api
    @slash_command("subreddit", description="Get a random post from a subreddit")
    @slash_option("subreddit", "Subreddit you want to grab from", OptionTypes.STRING, required=True)
    @slash_option("sort", "How you want to sort the subreddit", OptionTypes.STRING, required=False, choices=[
        SlashCommandChoice("Hot", "hot"),
        SlashCommandChoice("New", "new"),
        SlashCommandChoice("Top", "top")
    ])
    async def random_reddit(self, ctx: InteractionContext, subreddit: str, sort: str = "hot"):
        await ctx.defer()
        async with Reddit(
                client_id=REDDIT_ID,
                client_secret=REDDIT_SECRET,
                user_agent="Scrapper by: u/glitchychan"
        ) as r:
            try:
                sub = await r.subreddit(subreddit)
                match sort:
                    case "hot":
                        posts = [submission async for submission in sub.hot(limit=30)]
                    case "new":
                        posts = [submission async for submission in sub.new(limit=30)]
                    case "top":
                        posts = [submission async for submission in sub.top(limit=30)]
            except asyncprawcore.exceptions.ResponseException as e:
                if e.response.status == 404:
                    return await ctx.send(f"Subreddit `{subreddit}` does not exist")
                self.logger.exception(f"Reddit gave a {e.response.status}", e)
                return await ctx.send(f"Reddit gave a {e.response.status}", ephemeral=True)

        post: Submission = random.choice(posts)

        if not post.is_self:
            self.logger.debug(f"Downloading media from Reddit Post: {post.url}")
            async with aiohttp.ClientSession() as sesssion:
                req = await sesssion.get(post.url)
                if req.status < 400:
                    file = BytesIO(await req.content.read())
                    file.seek(0)

                    if post.url.startswith("https://v.redd.it/"):
                        file_extension = "mp4"
                    else:
                        file_extension = mimetypes.guess_extension(req.headers['content-type'])

                attachment = File(file=file, file_name=f"{uuid.uuid4()}.{file_extension}")

            # TODO: Add better formatting for image/video posts
            # TODO: Add formatting for Libreddit or Reddit links
            await ctx.send(f"{post.selftext}", files=[attachment])
        else:
            # TODO: Implement what happens when post is a text only post
            await ctx.send("Not implemented")

    @slash_command(name="8ball", description="It's an 8ball")
    @slash_option("question", "Question you want to ask the eight ball", OptionTypes.STRING, required=True)
    async def eight_ball(self, ctx: InteractionContext, question: str):
        responses = ['As I see it, yes.',
                     'Ask again later.',
                     'Better not tell you now.',
                     'Cannot predict now.',
                     'Concentrate and ask again.',
                     'Dont count on it.',
                     'It is certain.',
                     'It is decidedly so.',
                     'Most likely.',
                     'My reply is no.',
                     'My sources say no.',
                     'Outlook not so good.',
                     'Outlook good.',
                     'Reply hazy, try again.',
                     'Signs point to yes.',
                     'Very doubtful.',
                     'Without a doubt.',
                     'Yes.',
                     'Yes - definitely.',
                     'You may rely on it.']

        eight_ball_emb = Embed(
            title="Magic 8 Ball",
            description=f"Question: {question}\n Answer: {random.choice(responses)}",
            color=Color.random()
        )

        await ctx.send(embeds=[eight_ball_emb])


def setup(client):
    Funny(client)
