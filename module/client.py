import json
import discord
import koreanbots
from discord.ext import commands
from light_uniquebots import LUBClient


class JBotClient(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix=self.prefix,
                         help_command=None,
                         intents=discord.Intents.all(),
                         allowed_mentions=discord.AllowedMentions(everyone=False))
        self.koreanbots = koreanbots.Client(self, self.get_setting("kbot_token"), postCount=not self.is_debug)
        self.uniquebots = LUBClient(bot=self, token=self.get_setting("ubot_token"))

    @staticmethod
    def get_setting(key):
        with open("config.json", "r", encoding="UTF-8") as f:
            return json.load(f).get(key)

    @property
    def is_debug(self):
        return self.get_setting("debug")

    async def prefix(self, bot, message):
        # DB 모듈 제작 이후 수정 예정
        return commands.when_mentioned_or("제이봇 ", "j!")(bot, message)

    def run(self):
        super().run(self.get_setting("dev_token" if self.is_debug else "token"))
