from discord.ext import commands
from module import JBotClient, AuthorEmbed, EmbedColor, Pager


class Help(commands.Cog):
    def __init__(self, bot: JBotClient):
        self.bot = bot

    @commands.command(name="도움", description="도움말 명령어에요.", aliases=["help", "도움말", "commands", "명령어"])
    async def help(self, ctx: commands.Context, *args):
        embed = AuthorEmbed(ctx.author,
                            title="제이봇 명령어 리스트",
                            description="필수로 채워야 하는 항목은 `[항목이름]`이고, 선택적이면 `(항목이름)`으로 표시돼요.",
                            color=EmbedColor.DEFAULT,
                            timestamp=ctx.message.created_at)
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
