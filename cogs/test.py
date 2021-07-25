from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, Pager, Cursor


class Test(commands.Cog, name="PRIVATE_테스트"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.command(name="페이저")
    async def pager_test(self, ctx):
        pager = Pager(self.bot, ctx.channel, ctx.author, ["페이지 1", "페이지 2", "페이지 3"], reply=ctx.message)
        await pager.start_flatten()

    @commands.command(name="쿨다운")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def cooldown_test(self, ctx):
        await ctx.send("굴")

    @commands.command(name="커서")
    async def cursor_test(self, ctx):
        cursor = Cursor(self.bot, ctx.message, [*range(1, 10+1)], base_embed=AuthorEmbed(ctx.author, title="커서 테스트"))
        _msg, selected = await cursor.start()
        await ctx.reply(str(selected))


def setup(bot):
    bot.add_cog(Test(bot))
