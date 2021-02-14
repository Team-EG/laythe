import discord
from discord.ext import commands
from module import JBotClient
from module import AuthorEmbed
from module import EmbedColor


class Core(commands.Cog):
    def __init__(self, bot: JBotClient):
        self.bot = bot

    @commands.command(name="cog")
    async def manage_cog(self, ctx: commands.Context, *args):
        if args:
            return await self.light_cog_manage(ctx, *args)

    async def light_cog_manage(self, ctx: commands.Context, action: str, name: str = None):
        base = AuthorEmbed(ctx.author,
                           title="Cog 관리",
                           timestamp=ctx.message.created_at,
                           display_footer=True)
        abort = base.copy()
        abort.title += " 취소"
        abort.color = EmbedColor.NEGATIVE
        ask = base.copy()
        ask.color = EmbedColor.NEUTRAL
        success = base.copy()
        success.title += " 실행 완료"
        success.color = EmbedColor.POSITIVE
        actions = ["load", "unload", "reload", "detach", "update"]
        if action not in actions:
            abort.description = "잘못된 액션 키워드입니다."
            return await ctx.reply(embed=abort)
        if name == "core":
            if action != "reload":
                abort.description = "코어 모듈은 리로드만 가능합니다."
                return await ctx.reply(embed=abort)
            ask.description = "정말로 코어 모듈을 리로드 할까요?\n" \
                              "잘못된 코어 모듈이 들어가있는 경우 봇에 문제가 생길 수 있습니다."
            msg = await ctx.reply(embed=ask)
            conf = await self.bot.confirm(ctx.author, msg)
            self.bot.loop.create_task(self.bot.safe_clear_reaction(msg))
            if not conf:
                abort.description = "코어 모듈 리로드가 취소되었습니다."
                return await msg.edit(embed=abort)
            self.bot.reload_extension("core.core")
            success.description = "코어 모듈 리로드가 완료되었습니다."
            return await msg.edit(embed=success)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("on_ready Fired.")


def setup(bot):
    bot.add_cog(Core(bot))
