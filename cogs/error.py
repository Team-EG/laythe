import sys
import time
import traceback
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor
from module.utils import parse_second, permission_translates


class Error(commands.Cog):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        ex = error.original if isinstance(error, commands.CommandInvokeError) else error
        tb = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        base = AuthorEmbed(ctx.author, title="이런! ", display_footer=True, color=EmbedColor.NEGATIVE, timestamp=ctx.message.created_at)
        if self.bot.is_debug:
            print(tb, file=sys.stderr)
        edited_tb = ("..." + tb[-1997:]) if len(tb) > 2000 else tb
        if isinstance(error, commands.CommandNotFound):
            return
        await ctx.message.add_reaction("⏰") if isinstance(error, commands.CommandOnCooldown) \
            else await ctx.message.add_reaction("⚠")
        report_required = False
        if isinstance(error, commands.NotOwner):
            base.title += "이 명령어는 Team EG 개발자만 사용할 수 있는 명령어에요."
        elif isinstance(error, commands.CommandOnCooldown):
            base.title += "아직 쿨다운이 끝나지 않았어요."
            base.description = f"{parse_second(round(error.retry_after))}만 더 기다려주세요."
        elif isinstance(error, commands.MissingPermissions):
            base.title += "이 명령어를 실행할 권한이 부족해요."
            base.description = f"이 명령어를 실행하기 위해 `{'`, `'.join([permission_translates.get(x, x) for x in error.missing_perms])}` 권한이 필요해요."
        elif isinstance(error, commands.BotMissingPermissions):
            base.title += "이 서버에서 제 권한이 이 명령어를 실행하기에는 부족해요."
            base.description = f"`{'`, `'.join([permission_translates.get(x, x) for x in error.missing_perms])}` 권한을 저에게 부여해주세요."
        elif isinstance(error, commands.MissingRequiredArgument):
            base.title += "빠진 필수 항목이 있어요."
            base.description = "해당 명령어의 정확한 사용법은 도움말 명령어를 다시 확인해보세요."
        elif isinstance(error, commands.BadArgument):
            base.title += "잘못된 형식이에요."
            base.description = "일부 항목의 값이 형식에 맞지 않거나 유저 또는 역할 등 디스코드 관련일 경우 존재하지 않는 것 같아요. 값을 다시 확인해주세요."
        else:
            base.title += "예기치 못한 오류가 발생했어요..."
            base.description = f"디버깅용 메시지: ```py\n{edited_tb}\n```"
            base.add_field(name="잠시만요!", value="이 오류 정보를 개발자에게 전송할까요? 오류 전송 시 오류 내용과 명령어를 실행한 메시지 내용이 전달돼요.")
            report_required = True
        msg = await ctx.reply(embed=base)
        if report_required:
            conf = await self.bot.confirm(ctx.author, msg)
            if conf:
                debug_format = f"===LAYTHE-DEBUG===\n" \
                               f"MSG: {ctx.message.content}\n" \
                               f"AUTHOR: {ctx.author} (ID: {ctx.author.id})\n" \
                               f"TRACEBACK:\n\n" \
                               f"{tb}\n" \
                               f"===END-DEBUG==="
                fname = f"traceback/{str(time.time()).split('.')[0]}.txt"
                with open(fname, "w", encoding="UTF-8") as f:
                    f.write(debug_format)
                await self.bot.get_channel(764359951266480189).send(f"새로운 오류가 저장되었습니다. (`{fname}`)")
                await msg.reply("성공적으로 오류 메시지를 전송했어요!")
            else:
                await msg.reply("전송을 취소했어요.")


def setup(bot):
    bot.add_cog(Error(bot))
