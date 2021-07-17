import discord
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor


class Level(commands.Cog, name="레벨"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, discord.TextChannel) or "laythe:leveloff" in (message.channel.topic or ""):
            return


def setup(bot):
    bot.add_cog(Level(bot))
