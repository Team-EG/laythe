import typing
import asyncio
import discord
from discord_slash import ComponentContext
from discord_slash.utils import manage_components
from . import LaytheClient


class Pager:
    next_emoji = "➡"
    prev_emoji = "⬅"
    stop_emoji = "⏹"
    emoji_list = [prev_emoji, stop_emoji, next_emoji]

    def __init__(self,
                 client: LaytheClient,
                 channel: typing.Union[discord.TextChannel, discord.DMChannel],
                 author: discord.Member,
                 pages: typing.List[typing.Union[str, discord.Embed]],
                 custom_emojis: list = None,
                 *, is_embed: bool = False,
                 reply: discord.Message = None,
                 timeout: int = 30):
        self.client = client
        self.channel = channel
        self.author = author
        self.pages = pages
        self.custom_emojis = custom_emojis or []
        self.is_embed = is_embed
        self.reply = reply
        self.timeout = timeout
        self.current = 0
        self.message = None  # Should be set later.
        self.full_emoji_list = self.emoji_list.copy() + self.custom_emojis.copy()

    @property
    def __max_page(self):
        return len(self.pages) - 1

    @property
    def current_page(self):
        return self.current + 1

    def next(self):
        self.current = self.current + 1 if self.current + 1 <= self.__max_page else 0
        return self.pages[self.current]

    def prev(self):
        self.current = self.current - 1 if self.current - 1 >= 0 else self.__max_page
        return self.pages[self.current]

    def start(self, as_generator: bool = False):
        if as_generator:
            return self.__start
        else:
            return self.start_flatten

    async def start_flatten(self):
        return_list = []
        async for x in self.__start():
            return_list.append(x)
        return return_list

    async def __start(self):
        func = self.channel.send if not self.reply else self.reply.reply
        self.message = await func(content=self.pages[0] if not self.is_embed else None, embed=self.pages[0] if self.is_embed else None)

        next_button = manage_components.create_button(style=1, label="다음", custom_id=f"next{self.message.id}", emoji=self.next_emoji)
        prev_button = manage_components.create_button(style=1, label="이전", custom_id=f"prev{self.message.id}", emoji=self.prev_emoji)
        stop_button = manage_components.create_button(style=2, custom_id=f"stop{self.message.id}", emoji=self.stop_emoji)
        action_row = manage_components.create_actionrow(prev_button, stop_button, next_button)

        await self.message.edit(components=[action_row])

        while not self.client.is_closed():
            try:
                ctx: ComponentContext = await manage_components.wait_for_component(
                    self.client,
                    [self.message],
                    action_row,
                    check=lambda comp_ctx: int(comp_ctx.author_id) == int(self.author.id),
                    timeout=self.timeout
                )

                await ctx.defer(edit_origin=True)

                if ctx.custom_id.startswith("stop"):
                    yield self.current_page
                    break

                elif ctx.custom_id.startswith("next"):
                    page = self.next()
                    await self.message.edit(content=page if not self.is_embed else None,
                                            embed=page if self.is_embed else None)

                elif ctx.custom_id.startswith("prev"):
                    page = self.prev()
                    await self.message.edit(content=page if not self.is_embed else None,
                                            embed=page if self.is_embed else None)

            except asyncio.TimeoutError:
                yield self.current_page
                break

        next_button = manage_components.create_button(style=1, label="다음", custom_id=f"next{self.message.id}", emoji=self.next_emoji, disabled=True)
        prev_button = manage_components.create_button(style=1, label="이전", custom_id=f"prev{self.message.id}", emoji=self.prev_emoji, disabled=True)
        stop_button = manage_components.create_button(style=2, custom_id=f"stop{self.message.id}", emoji=self.stop_emoji, disabled=True)
        action_row = manage_components.create_actionrow(prev_button, stop_button, next_button)

        await self.message.edit(components=[action_row])
