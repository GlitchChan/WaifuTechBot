import asyncio
import textwrap
from typing import Optional, List, Union

from attr import define, field
from naff import (
    ComponentCommand,
    Button,
    ActionRow,
    spread_to_rows,
    Select,
    SelectOption,
    ComponentContext,
    Message,
    Client,
    Embed,
    PartialEmoji,
    process_emoji
)
from naff.client.utils import export_converter
from naff.ext.paginators import Paginator, Page

__all__ = (
    "MeguminPaginator",
    "StringPage",
)


@define(kw_only=False)
class StringPage:
    """Modified NAFF Page to add string support"""
    content: str = field(kw_only=True, default="")
    """The content of the page."""
    prefix: str = field(kw_only=True, default="")
    """Content that is prepended to the page."""
    suffix: str = field(kw_only=True, default="")
    """Content that is appended to the page."""

    @property
    def get_summary(self) -> str:
        """Get the short version of the page content."""
        return self.title or textwrap.shorten(self.content, 40, placeholder="...")

    def to_string(self) -> str:
        """Process to page into a complex string"""
        return f"{self.prefix}\n\n {self.content}\n\n {self.suffix}"

    def set_suffix(self, suffix: str) -> None:
        self.suffix = suffix


@define(kw_only=False)
class MeguminPaginator(Paginator):
    """Modified NAFF Paginator to add customizations to"""
    pages: List[Page | Embed | StringPage] = field(factory=list, kw_only=True)
    """The pages this paginator holds"""
    show_skip_to_button: bool = field(default=True)
    """Should a `Skip To` button be shown"""
    skip_button_emoji: Optional[Union["PartialEmoji", dict, str]] = field(
        default="🚀", metadata=export_converter(process_emoji)
    )
    """The emoji to use for the skip button"""

    def __attrs_post_init__(self) -> None:
        self.client.add_component_callback(
            ComponentCommand(
                name=f"Paginator:{self._uuid}",
                callback=self._on_button,
                listeners=[
                    f"{self._uuid}|select",
                    f"{self._uuid}|first",
                    f"{self._uuid}|back",
                    f"{self._uuid}|callback",
                    f"{self._uuid}|next",
                    f"{self._uuid}|last",
                    f"{self._uuid}|skip_to"
                ],
            )
        )

    @classmethod
    def create_from_string(
            cls, client: "Client", *pages: StringPage, timeout: int = 0) -> "MeguminPaginator":
        """
        Create a paginator system from a string.

        Args:
            client: A reference to the NAFF client
            pages: StringPages to use
            timeout: A timeout to wait before closing the paginator

        Returns:
            A paginator system
        """
        return cls(client, pages=pages, timeout_interval=timeout)

    def create_components(self, disable: bool = False) -> List[ActionRow]:
        """
        Create the components for the paginator message.

        Args:
            disable: Should all the components be disabled?

        Returns:
            A list of ActionRows

        """
        output = []

        if self.show_select_menu:
            current = self.pages[self.page_index]
            output.append(
                Select(
                    [
                        SelectOption(f"{i+1} {p.get_summary if isinstance(p, Page) else p.title}", str(i))
                        for i, p in enumerate(self.pages)
                    ],
                    custom_id=f"{self._uuid}|select",
                    placeholder=f"{self.page_index+1} {current.get_summary if isinstance(current, Page) else current.title}",
                    max_values=1,
                    disabled=disable,
                )
            )

        if self.show_first_button:
            output.append(
                Button(
                    self.default_button_color,
                    emoji=self.first_button_emoji,
                    custom_id=f"{self._uuid}|first",
                    disabled=disable or self.page_index == 0,
                )
            )
        if self.show_back_button:
            output.append(
                Button(
                    self.default_button_color,
                    emoji=self.back_button_emoji,
                    custom_id=f"{self._uuid}|back",
                    disabled=disable or self.page_index == 0,
                )
            )

        if self.show_callback_button:
            output.append(
                Button(
                    self.default_button_color,
                    emoji=self.callback_button_emoji,
                    custom_id=f"{self._uuid}|callback",
                    disabled=disable,
                )
            )

        if self.show_next_button:
            output.append(
                Button(
                    self.default_button_color,
                    emoji=self.next_button_emoji,
                    custom_id=f"{self._uuid}|next",
                    disabled=disable or self.page_index >= len(self.pages) - 1,
                )
            )
        if self.show_last_button:
            output.append(
                Button(
                    self.default_button_color,
                    emoji=self.last_button_emoji,
                    custom_id=f"{self._uuid}|last",
                    disabled=disable or self.page_index >= len(self.pages) - 1,
                )
            )
        if self.show_skip_to_button:
            output.append(
                Button(
                    self.default_button_color,
                    emoji=self.skip_button_emoji,
                    custom_id=f"{self._uuid}|skip_to",
                    disabled=disable or self.page_index >= len(self.pages) - 1,
                )
            )

        return spread_to_rows(*output)

    def to_dict(self) -> dict:
        """Convert this paginator into a dictionary for sending."""
        page = self.pages[self.page_index]

        if isinstance(page, StringPage):
            page.set_suffix(f"Page {self.page_index + 1}/{len(self.pages)}")
            page = page.to_string()
            return {"content": page, "components": [c.to_dict() for c in self.create_components()]}

        if isinstance(page, Page):
            page = page.to_embed()
            if not page.title and self.default_title:
                page.title = self.default_title
        if not page.footer:
            page.set_footer(f"Page {self.page_index + 1}/{len(self.pages)}")
        if not page.color:
            page.color = self.default_color

        return {"embeds": [page.to_dict()], "components": [c.to_dict() for c in self.create_components()]}

    async def skip_to_page(self, ctx: ComponentContext):
        skip_message = await ctx.send("What page would you like to skip to")
        try:
            selection = await self.client.wait_for("on_message_create", checks=lambda m: all([
                m.message.channel.id == self.message.channel.id,
                m.message.author.id == self.author_id
            ]), timeout=60)
            page = int(selection.message.content)
            if 1 <= page <= len(self.pages):
                self.page_index = page - 1
            await asyncio.gather(skip_message.delete(), selection.message.delete(), self.update())
        except (asyncio.TimeoutError, ValueError):
            error = await ctx.send("Either page out of rage or a timeout happened")
            await asyncio.sleep(3)
            await asyncio.gather(skip_message.delete(), error.delete())

    async def _on_button(self, ctx: ComponentContext, *args, **kwargs) -> Optional[Message]:
        if ctx.author.id == self.author_id:
            if self._timeout_task:
                self._timeout_task.ping.set()
            match ctx.custom_id.split("|")[1]:
                case "first":
                    self.page_index = 0
                case "last":
                    self.page_index = len(self.pages) - 1
                case "next":
                    if (self.page_index + 1) < len(self.pages):
                        self.page_index += 1
                case "back":
                    if (self.page_index - 1) >= 0:
                        self.page_index -= 1
                case "skip_to":
                    return await self.skip_to_page(ctx)
                case "select":
                    self.page_index = int(ctx.values[0])
                case "callback":
                    if self.callback:
                        return await self.callback(ctx)

            await ctx.edit_origin(**self.to_dict())
        else:
            if self.wrong_user_message:
                return await ctx.send(self.wrong_user_message, ephemeral=True)
            else:
                # silently ignore
                return await ctx.defer(edit_origin=True)
