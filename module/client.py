import json
import typing
import asyncio
import logging
import datetime
import aiohttp
import discord
from contextlib import suppress
from discord.ext import commands
from discord_slash import SlashCommand
from .database import LaytheDB
from extlib import BotList, SpellChecker


class LaytheClient(commands.AutoShardedBot):
    def __init__(self, logger: logging.Logger, **kwargs):
        super().__init__(command_prefix=self.prefix,
                         help_command=None,
                         intents=discord.Intents.all(),
                         allowed_mentions=discord.AllowedMentions(everyone=False))
        self.logger = logger
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.botlist = BotList(self, self.get_setting("kbot_token"), self.get_setting("ubot_token"), run_update=not self.is_debug)
        self.spell = SpellChecker(self.session)
        self.slash = SlashCommand(self)
        self.db = LaytheDB(self.get_setting("dbhost"),
                           self.get_setting("dbport"),
                           self.get_setting("dbid"),
                           self.get_setting("dbpw"),
                           self.get_setting("tgt_db"))
        self.loop.create_task(self.init_all_ext())

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
        return commands.when_mentioned_or("레이테 ", "laythe ", "Laythe", "l!", "L!", "ㅣ!")(bot, message)

    async def init_all_ext(self):
        await self.wait_until_ready()
        await self.db.login()

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

    async def safe_clear_reactions(self, message: discord.Message):
        reactions = message.reactions
        try:
            await message.clear_reactions()
        except discord.Forbidden:
            [await x.remove(self.user) for x in reactions]

    @staticmethod
    async def safe_clear_reaction(reaction: discord.Reaction, user: typing.Union[discord.User, discord.Member]):
        with suppress(discord.Forbidden):
            await reaction.remove(user)

    def run(self):
        super().run(self.get_setting("dev_token" if self.is_debug else "token"))

    async def close(self):
        self.db.close()
        await self.session.close()
        await super().close()
