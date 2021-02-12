import discord
from discord.ext import commands
from module import JBotClient
from module import AuthorEmbed
from module import EmbedColor


class Core(commands.Cog):
    def __init__(self, bot: JBotClient):
        self.bot = bot

    @commands.command(name="cog")
    async def manage_cog(self, ctx, *args):
        if args:
            return await self.light_cog_manage(ctx, *args)

    async def light_cog_manage(self, ctx, name, action):
        abort = AuthorEmbed(ctx.author,
                            title="Cog 관리 취소됨",
                            timestamp=ctx.message.created_at,
                            color=EmbedColor.NEGATIVE)
        ask = AuthorEmbed(ctx.author,
                          title="Cog 관리 취소됨",
                          timestamp=ctx.message.created_at,
                          color=EmbedColor.NEUTRAL)
        actions = ["load", "unload", "reload"]
        if name == "core":
            if action != "reload":
                abort.description = "코어 모듈은 리로드만 가능합니다."
                return await ctx.send(embed=abort)
            else:
                pass


def setup(bot):
    bot.add_cog(Core(bot))
