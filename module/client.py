import json
import typing
import asyncio
import logging
import datetime
import discord
import koreanbots
from contextlib import suppress
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

    @staticmethod
    def parse_second(time: int):
        parsed_time = ""
        day = time // (24 * 60 * 60)
        time -= day * (24 * 60 * 60)
        hour = time // (60 * 60)
        time -= hour * (60 * 60)
        minute = time // 60
        time -= minute * 60
        if day:
            parsed_time += f"{day}일 "
        if hour:
            parsed_time += f"{hour}시간 "
        if minute:
            parsed_time += f"{minute}분 "
        parsed_time += f"{time}초"
        return parsed_time

    @staticmethod
    def parse_bytesize(bytesize: float):
        gb = round(bytesize / (1000*1000*1000), 1)
        if gb < 1:
            mb = round(bytesize / (1000*1000), 1)
            if mb < 1:
                return f"{bytesize}KB"
            return f"{mb}MB"
        return f"{gb}GB"

    def run(self):
        super().run(self.get_setting("dev_token" if self.is_debug else "token"))
