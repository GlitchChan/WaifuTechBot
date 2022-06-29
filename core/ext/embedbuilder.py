from datetime import datetime
from naff import Embed, Color
from typing import Union, List, Optional


async def embed_builder(
        description: Optional[str] = None,
        title: Optional[str] = None,
        color: Optional[Union[Color, dict, tuple, list, str, int]] = Color.random(),
        fields: Optional[List[List[str, str, bool]]] = None,
        thumbnail: Optional[str] = None,
        author: Optional[List[str, str]] = None,
        footer: Optional[List[str, Optional[str]]] = None,
        url: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        image: Optional[str] = None,
) -> Embed:
    """ Quickly build embeds with one function call

    :param description: The description of the embed
    :param title: The title of the embed
    :param color: The colour of the embed
    :param fields: A list of fields to go in the embed
    :param thumbnail: The thumbnail of the embed
    :param author: The author of the embed
    :param footer: The footer of the embed
    :param url: The url the embed should direct to when clicked
    :param timestamp: Timestamp of embed content
    :param image: The image of the embed
    """

    embed = Embed(
        title=title,
        description=description,
        color=color,
        url=url,
        timestamp=timestamp
    )
    if fields:
        for field in fields:
            embed.add_field(field[0], field[1], bool(field[2]))
    if thumbnail:
        embed.set_thumbnail(thumbnail)
    if author:
        embed.set_author(author[0], author[1])
    if footer:
        embed.set_footer(footer[0], footer[1])
    if image:
        embed.set_image(image)

    return embed
