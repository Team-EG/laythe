from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, Pager


class Help(commands.Cog, name="도움말"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.command(name="도움", description="도움말 명령어에요.", aliases=["help", "도움말", "commands", "명령어"])
    async def help(self, ctx: commands.Context):
        embed = AuthorEmbed(ctx.author,
                            title="Laythe 명령어 리스트",
                            description="필수로 채워야 하는 항목은 `[항목이름:타입]`이고, 선택적이면 `(항목이름:타입)`으로 표시돼요.",
                            color=EmbedColor.DEFAULT,
                            timestamp=ctx.message.created_at)
        for name, cog in self.bot.cogs.items():
            if not cog.get_commands():
                continue
            embed.add_field(name=name, value=', '.join([f"`{x.name}`" for x in cog.get_commands()]), inline=False)
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
