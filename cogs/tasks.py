import discord
import asyncio
from discord.ext import commands, tasks
from module import LaytheClient


class Tasks(commands.Cog, name="태스크"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot
        self.update_cache.start()
        self.change_presence.start()

    def cog_unload(self):
        self.update_cache.cancel()

    @tasks.loop(minutes=5)
    async def update_cache(self):
        if self.bot.db_ready:
            await self.bot.cache_manager.update_cache()
            self.bot.logger.info("DB cache updated.")

    @tasks.loop()
    async def change_presence(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            texts = ["`레이테 도움말` 명령어로 레이테의 명령어를 확인해보세요!",
                     f"{len(self.bot.guilds)}개 서버에서 사용",
                     f"{len(self.bot.users)}명 유저들이 사용"]
            for x in texts:
                await self.bot.change_presence(activity=discord.Game(name=x))
                await asyncio.sleep(15)


def setup(bot):
    bot.add_cog(Tasks(bot))
