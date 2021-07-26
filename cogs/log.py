import discord
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, GuildEmbed, EmbedColor


class Log(commands.Cog, name="로깅"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.attachments:
            [await self.bot.execute_guild_log(message.guild, content="로그 저장용 메시지입니다: "+x.url, delete_after=1) for x in message.attachments]


def setup(bot):
    bot.add_cog(Log(bot))
