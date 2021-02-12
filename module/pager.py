import discord
from . import JBotClient


class Pager:
    next_emoji = "➡"
    prev_emoji = "⬅"
    stop_emoji = "⏹"

    def __init__(self,
                 client: JBotClient,
                 channel: discord.TextChannel,
                 author: discord.Member,
                 pages: list,
                 *, is_embed: bool = False):
        self.client = client
        self.channel = channel
        self.author = author
        self.pages = pages
        self.is_embed = is_embed
        self.current = 0
        self.message = None # Should be set later.

    @property
    def max_page(self):
        return len(self.pages) - 1

    def next(self):
        self.current = self.current + 1 if self.current + 1 <= self.max_page else 0
        return self.pages[self.current]

    def prev(self):
        self.current = self.current - 1 if self.current - 1 >= 0 else self.max_page
        return self.pages[self.current]

    async def start(self):
        self.message = await self.channel.send(self.pages[0] if not self.is_embed else None,
                                               embed=self.pages[0] if self.is_embed else None)
        self.client.loop
        while not self.client.is_closed():
            pass
