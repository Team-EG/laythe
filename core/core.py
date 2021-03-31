import os
import sys
import traceback
from discord.ext import commands
from module import JBotClient, AuthorEmbed, EmbedColor


class Core(commands.Cog):
    def __init__(self, bot: JBotClient):
        self.bot = bot

    @commands.command(name="cog")
    @commands.is_owner()
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
        actions = ["load", "unload", "reload", "detach", "attach", "update"]
        name_not_req = ["detach", "attach", "update"]

        if action not in actions:
            abort.description = "잘못된 액션 키워드입니다."
            return await ctx.reply(embed=abort)
        if not name and action not in name_not_req:
            abort.description = f"액션 `{action}`은(는) Cog 이름이 필수입니다."
            return await ctx.reply(embed=abort)
        if name and action in name_not_req:
            abort.description = f"액션 `{action}`은(는) Cog 이름을 요구하지 않습니다."
            return await ctx.reply(embed=abort)

        if action in name_not_req or name == "-all":
            if action not in name_not_req:
                action = {"load": "attach", "unload": "detach", "reload": "update"}[action]
            act = {"detach": ["언로드", self.bot.unload_extension],
                   "attach": ["로드", self.bot.load_extension],
                   "update": ["리로드", self.bot.reload_extension]}
            selected = act[action]
            ask.description = f"정말로 Cog 전체를 {selected[0]} 할까요?"
            msg = await ctx.reply(embed=ask)
            conf = await self.bot.confirm(ctx.author, msg)
            self.bot.loop.create_task(self.bot.safe_clear_reactions(msg))
            if not conf:
                abort.description = f"Cog 전체 {selected[0]}가 취소되었습니다."
                return await msg.edit(embed=abort)
            [selected[1](f"cogs.{x.replace('.py', '')}") for x in os.listdir("cogs") if x.endswith('.py') and not x.startswith("_")]
            success.description = f"Cog 전체 {selected[0]}가 완료되었습니다."
            return await msg.edit(embed=success)

        if name == "core":
            if action != "reload":
                abort.description = "코어 모듈은 리로드만 가능합니다."
                return await ctx.reply(embed=abort)
            ask.description = "정말로 코어 모듈을 리로드 할까요?\n" \
                              "잘못된 코어 모듈이 들어가있는 경우 봇에 문제가 생길 수 있습니다."
            msg = await ctx.reply(embed=ask)
            conf = await self.bot.confirm(ctx.author, msg)
            self.bot.loop.create_task(self.bot.safe_clear_reactions(msg))
            if not conf:
                abort.description = "코어 모듈 리로드가 취소되었습니다."
                return await msg.edit(embed=abort)
            self.bot.reload_extension("core.core")
            success.description = "코어 모듈 리로드가 완료되었습니다."
            return await msg.edit(embed=success)

        if name not in [x.replace(".py", "") for x in os.listdir('cogs')]:
            abort.description = "존재하지 않는 Cog 이름입니다."
            return await ctx.reply(embed=abort)

        act = {"unload": ["언로드", self.bot.unload_extension],
               "load": ["로드", self.bot.load_extension],
               "reload": ["리로드", self.bot.reload_extension]}
        selected = act[action]
        ask.description = f"정말로 Cog `{name}`을(를) {selected[0]} 할까요?"
        msg = await ctx.reply(embed=ask)
        conf = await self.bot.confirm(ctx.author, msg)
        self.bot.loop.create_task(self.bot.safe_clear_reactions(msg))
        if not conf:
            abort.description = f"Cog `{name}` {selected[0]}가 취소되었습니다."
            return await msg.edit(embed=abort)
        selected[1](f"cogs.{name}")
        success.description = f"Cog `{name}` {selected[0]}가 완료되었습니다."
        return await msg.edit(embed=success)

    @manage_cog.error
    async def on_manage_cog_error(self, ctx, ex):
        print(''.join(traceback.format_exception(type(ex), ex, ex.__traceback__)), file=sys.stderr)
        embed = AuthorEmbed(ctx.author,
                            title="이런! Cog 작업중 오류가 발생했어요...",
                            description=f"```py\n{ex}\n```",
                            timestamp=ctx.message.created_at,
                            color=EmbedColor.NEGATIVE,
                            display_footer=True)
        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("on_ready Fired.")


def setup(bot):
    bot.add_cog(Core(bot))
