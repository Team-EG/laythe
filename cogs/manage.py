from discord.ext import commands
from module import JBotClient, AuthorEmbed, EmbedColor, Pager


class Manage(commands.Cog):
    def __init__(self, bot: JBotClient):
        self.bot = bot

    @commands.group(name="정리", description="메세지를 대량으로 삭제해요.", aliases=["purge"])
    async def purge(self, ctx: commands.Context):
        pass


def setup(bot):
    bot.add_cog(Manage(bot))
