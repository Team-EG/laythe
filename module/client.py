import json
import asyncio
import logging
import datetime
import discord
import koreanbots
from discord.ext import commands
from light_uniquebots import LUBClient


class JBotClient(commands.AutoShardedBot):
    def __init__(self, logger: logging.Logger, **kwargs):
        super().__init__(command_prefix=self.prefix,
                         help_command=None,
                         intents=discord.Intents.all(),
                         allowed_mentions=discord.AllowedMentions(everyone=False))
        self.logger = logger
        self.koreanbots = koreanbots.Client(self, self.get_setting("kbot_token"), postCount=not self.is_debug)
        self.uniquebots = LUBClient(bot=self, token=self.get_setting("ubot_token"), run_update=False)

    @staticmethod
    def get_setting(key):
        with open("config.json", "r", encoding="UTF-8") as f:
            return json.load(f).get(key)

    @property
    def kst(self):
        return datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))

    @property
    def is_debug(self):
        return self.get_setting("debug")

    async def prefix(self, bot, message):
        # DB 모듈 제작 이후 수정 예정
        return commands.when_mentioned_or("제이봇 ", "j!")(bot, message)

    async def init_lava(self):
        raise NotImplementedError

    async def confirm(self, author: discord.User, message: discord.Message, timeout=30):
        emoji_list = ["⭕", "❌"]
        [self.loop.create_task(message.add_reaction(x)) for x in emoji_list]
        try:
            reaction = (
                await self.wait_for(
                    "reaction_add",
                    timeout=timeout,
                    check=lambda r, u: r.message.id == message.id and str(r.emoji) in emoji_list and u == author
                )
            )[0]
            return str(reaction.emoji) == emoji_list[0]
        except asyncio.TimeoutError:
            return None

    async def safe_clear_reaction(self, message: discord.Message):
        reactions = message.reactions
        try:
            await message.clear_reactions()
        except discord.Forbidden:
            [await x.remove(self.user) for x in reactions]

    def run(self):
        super().run(self.get_setting("dev_token" if self.is_debug else "token"))
