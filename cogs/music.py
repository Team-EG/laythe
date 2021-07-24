from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, Pager


class Music(commands.Cog, name="음악"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot


def setup(bot):
    bot.add_cog(Music(bot))
