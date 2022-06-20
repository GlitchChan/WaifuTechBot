from NHentai import NHentaiAsync
from NHentai.entities.doujin import Doujin
from naff import Extension, InteractionContext, OptionTypes, Embed, slash_command, slash_option
from pygelbooru import Gelbooru
from pygelbooru.gelbooru import GelbooruImage

from config import GELBOORU_ID, GELBOORU_KEY
from core import Megumin, get_logger
from core.ext import MeguminPaginator, StringPage


class Cunny(Extension):
    def __init__(self, client: Megumin):
        self.client: Megumin = client
        self.nhentai_client = NHentaiAsync()
        self.gel = Gelbooru(GELBOORU_KEY, GELBOORU_ID)
        self.logger = get_logger(__class__.__name__)
        self.logger.info(f"{__class__.__name__} Cog loaded")

    @slash_command("nhentai",
                   description="Nhentai commands",
                   sub_cmd_name="random",
                   sub_cmd_description="Get a random doujin from nhentai",
                   nsfw=True
                   )
    async def nhentai_random(self, ctx: InteractionContext):
        doujin: Doujin = await self.nhentai_client.get_random()
        tags = [tag.name for tag in doujin.tags]

        doujin_embed = Embed(title=doujin.title.pretty, color=0xEC2854, url=doujin.url, description=", ".join(tags))
        doujin_embed.set_image(doujin.cover.src)

        await ctx.send(embed=doujin_embed)

    @slash_command("nhentai",
                   description="Nhentai commands",
                   sub_cmd_name="read",
                   sub_cmd_description="Read a doujin from nhentai",
                   nsfw=True
                   )
    @slash_option("hentai_id", "Id of the hentai you want to read", OptionTypes.STRING, required=True)
    async def read_hentai(self, ctx: InteractionContext, hentai_id: str):
        doujin: Doujin = await self.nhentai_client.get_doujin(hentai_id)

        pages = []

        for page in doujin.images:
            page_embed = Embed(title=doujin.title.pretty, color=0xEC2854, url=doujin.url)
            page_embed.set_image(page.src)
            pages.append(page_embed)

        doujin_reader = MeguminPaginator.create_from_embeds(self.client, *pages, timeout=60)
        if len(doujin_reader.pages) <= 25:
            doujin_reader.show_select_menu = True
        await doujin_reader.send(ctx)

    @slash_command("nsfw",
                   description="NSFW commands",
                   group_name="gelbooru",
                   group_description="Gelbooru Commands",
                   sub_cmd_name="random",
                   sub_cmd_description="Fetches a random post from Gelbooru",
                   nsfw=True
                   )
    @slash_option("tags", "Tags you want to include in the search, *space seperated*", OptionTypes.STRING, required=True)
    @slash_option("excluded_tags", "Tags you want excluded from the search", OptionTypes.STRING, required=False)
    async def random_gelbooru(self, ctx: InteractionContext, tags: str, excluded_tags: str = None):
        tags = tags.replace(",", "").split(' ')
        excluded_tags = excluded_tags.split(' ') if excluded_tags else None

        await ctx.defer()
        result: GelbooruImage = await self.gel.random_post(tags=tags, exclude_tags=excluded_tags)

        if not result:
            return await ctx.send("Nobody here but us chickens!", ephemeral=True)

        await ctx.send(f"[Gelbooru Random]({result.file_url})")

    @slash_command("nsfw",
                   description="NSFW commands",
                   group_name="gelbooru",
                   group_description="Gelbooru Commands",
                   sub_cmd_name="browse",
                   sub_cmd_description="Browse around Gelbooru",
                   nsfw=True
                   )
    @slash_option("tags", "Tags you want to include in the search, *space seperated*", OptionTypes.STRING, required=True)
    @slash_option("excluded_tags", "Tags you want excluded from the search", OptionTypes.STRING, required=False)
    @slash_option("start_page", "What page you would like to start at", OptionTypes.INTEGER, required=False)
    async def browse_gelbooru(self, ctx: InteractionContext, tags: str, excluded_tags: str = None, start_page: int = 0):
        tags = tags.replace(",", "").split(' ')
        excluded_tags = excluded_tags.split(' ') if excluded_tags else None

        await ctx.defer()

        result = await self.gel.search_posts(tags=tags, exclude_tags=excluded_tags, page=start_page)

        if not result:
            return await ctx.send("Nobody here but us chickens!", ephemeral=True)

        pages = []

        for image in result:
            page = StringPage(content=f"[Browsing Gelbooru]({image.file_url})")
            pages.append(page)

        gel_browse = MeguminPaginator.create_from_string(self.client, *pages, timeout=60)
        await gel_browse.send(ctx)


def setup(client):
    Cunny(client)
