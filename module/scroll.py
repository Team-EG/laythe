import typing
import asyncio
import discord
from . import JBotClient


class Scroll:
    emoji_list = []

    def __init__(self,
                 client: JBotClient,
                 channel: typing.Union[discord.TextChannel, discord.DMChannel],
                 author: discord.Member,
                 items: list,
                 custom_emojis: list = None,
                 *, is_embed: bool = False,
                 reply: discord.Message = None,
                 timeout: int = 30):
        self.client = client
        self.channel = channel
        self.author = author
        self.items = items
        self.custom_emojis = custom_emojis or []
        self.is_embed = is_embed
        self.reply = reply
        self.timeout = timeout
        self.current = 0
        self.message = None  # Should be set later.
        self.full_emoji_list = self.emoji_list.copy() + self.custom_emojis.copy()

    @property
    def __max_page(self):
        return len(self.items) - 1

    @property
    def current_page(self):
        return self.current + 1

    def next(self):
        self.current = self.current + 1 if self.current + 1 <= self.__max_page else 0
        return self.items[self.current]

    def prev(self):
        self.current = self.current - 1 if self.current - 1 >= 0 else self.__max_page
        return self.items[self.current]

    def show_nums(self):
        to_return = []
        return to_return
