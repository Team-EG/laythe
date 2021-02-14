from discord.ext import commands


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.reply("Pong!")

    @commands.command(name="raise")
    async def _raise(self, ctx):
        await ctx.reply([][2])


def setup(bot):
    bot.add_cog(Basic(bot))
