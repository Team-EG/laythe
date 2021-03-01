from discord.ext import commands
from module import JBotClient, AuthorEmbed, EmbedColor


class Utils(commands.Cog):
    def __init__(self, bot: JBotClient):
        self.bot = bot


def setup(bot):
    bot.add_cog(Utils(bot))
