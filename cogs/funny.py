import random
import uuid
from io import BytesIO

import aiohttp
import asyncprawcore.exceptions
import naff
from asyncpraw import Reddit
from asyncpraw.models import Submission
from naff import (
    Extension,
    OptionTypes,
    InteractionContext,
    Embed,
    Color,
    SlashCommandChoice,
    slash_command,
    slash_option,
    File
)

from secrets import REDDIT_ID, REDDIT_SECRET
from core import Megumin, get_logger


class Funny(Extension):
    def __init__(self, client: Megumin):
        self.client = client
        self.logger = get_logger(__class__.__name__)
        self.logger.info(f"{__class__.__name__} Cog loaded")

    @slash_command("rate_me", description="I will rate the person you give")
    @slash_option("ratee", "Thing you want to rate", OptionTypes.STRING, required=False)
    async def rate_me(self, ctx: InteractionContext, ratee: str):
        rating = hash(ratee) % 10
        await ctx.send(f"I rate {ratee} a {rating}/10")

    # TODO: Testing
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

                post: Submission = random.choice(posts)
                await post.load()

                if post.over_18 and not ctx.channel.nsfw:
                    return await ctx.send("This post is NSFW and you aren't in a NSFW channel")

                emb = Embed(color="#FF4500", timestamp=post.created_utc, description=post.selftext)
                emb.set_author(post.title)

                if not post.is_self:
                    if post.url.startswith("https://v.redd.it/"):
                        self.logger.debug(f"Downloading media from Reddit Post: {post.url}")
                        async with aiohttp.ClientSession() as session:
                            req = await session.get(post.url)
                            if req.status < 400:
                                file = BytesIO(await req.content.read())
                                file.seek(0)
                                file_extension = 'mp4'
                                attachment = File(file=file, file_name=f"{uuid.uuid4()}.{file_extension}")
                                return await ctx.send(embeds=[emb], files=[attachment])
                    else:
                        emb.set_image(post.url)
                        return await ctx.send(embeds=[emb])
                else:
                    await ctx.send(embeds=[emb])

            except asyncprawcore.exceptions.ResponseException as e:
                if e.response.status == 404:
                    return await ctx.send(f"Subreddit `{subreddit}` does not exist")
                self.logger.exception(f"Reddit gave a {e.response.status}", e)
                return await ctx.send(f"Reddit gave a {e.response.status}", ephemeral=True)

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
