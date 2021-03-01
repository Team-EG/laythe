import typing
import asyncio
import discord
from . import JBotClient


class Pager:
    next_emoji = "➡"
    prev_emoji = "⬅"
    stop_emoji = "⏹"
    emoji_list = [prev_emoji, stop_emoji, next_emoji]

    def __init__(self,
                 client: JBotClient,
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

    async def start_flatten(self):
        return_list = []
        async for x in self.start():
            return_list.append(x)
        return return_list

    async def start(self):
        func = self.channel.send if not self.reply else self.reply.reply
        self.message = await func(self.pages[0] if not self.is_embed else None,
                                  embed=self.pages[0] if self.is_embed else None)
        [self.client.loop.create_task(self.message.add_reaction(x)) for x in self.full_emoji_list]
        while not self.client.is_closed():
            try:
                reaction = (await self.client.wait_for("reaction_add",
                                                       check=lambda r, u: r.message.id == self.message.id and
                                                                          str(r.emoji) in self.full_emoji_list and
                                                                          u.id == self.author.id,
                                                       timeout=self.timeout))[0]
                if str(reaction.emoji) in self.custom_emojis:
                    self.client.loop.create_task(self.client.safe_clear_reaction(reaction, self.author))
                    yield reaction

                elif str(reaction.emoji) == self.stop_emoji:
                    self.client.loop.create_task(self.client.safe_clear_reactions(self.message))
                    yield self.current_page
                    break

                elif str(reaction.emoji) == self.next_emoji:
                    page = self.next()
                    await self.message.edit(content=page if not self.is_embed else None,
                                            embed=page if self.is_embed else None)
                    self.client.loop.create_task(self.client.safe_clear_reaction(reaction, self.author))

                elif str(reaction.emoji) == self.prev_emoji:
                    page = self.prev()
                    await self.message.edit(content=page if not self.is_embed else None,
                                            embed=page if self.is_embed else None)
                    self.client.loop.create_task(self.client.safe_clear_reaction(reaction, self.author))

            except asyncio.TimeoutError:
                self.client.loop.create_task(self.client.safe_clear_reactions(self.message))
                yield self.current_page
                break
