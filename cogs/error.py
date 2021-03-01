import sys
import time
import traceback
from discord.ext import commands
from module import JBotClient, AuthorEmbed, EmbedColor


class Error(commands.Cog):
    def __init__(self, bot: JBotClient):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        base = AuthorEmbed(ctx.author, title="이런!", display_footer=True, color=EmbedColor.NEGATIVE, timestamp=ctx.message.created_at)
        if self.bot.is_debug:
            return print(tb, file=sys.stderr)
        edited_tb = ("..." + tb[-1997:]) if len(tb) > 2000 else tb
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.NotOwner):
            base.title += " 이 명령어는 Team EG 개발자만 사용할 수 있는 명령어에요."
            await ctx.reply(embed=base)
        else:
            base.title += " 예기치 못한 오류가 발생했어요..."
            base.description = f"디버깅용 메시지: ```py\n{edited_tb}\n```"
            base.add_field(name="잠시만요!", value="이 오류 정보를 개발자에게 전송할까요? 오류 전송 시 오류 내용과 명령어를 실행한 메시지 내용이 전달돼요.")
            msg = await ctx.reply(embed=base)
            conf = await self.bot.confirm(ctx.author, msg)
            if conf:
                debug_format = f"===JBOT-DEBUG===\n" \
                               f"MSG: {ctx.message.content}\n" \
                               f"AUTHOR: {ctx.author} (ID: {ctx.author.id})\n" \
                               f"TRACEBACK:\n\n" \
                               f"{tb}\n" \
                               f"===END-DEBUG==="
                fname = f"traceback/{str(time.time()).split('.')[0]}.txt"
                with open(fname, "w", encoding="UTF-8") as f:
                    f.write(debug_format)
                await self.bot.get_channel(696562545489870861).send(f"새로운 오류가 저장되었습니다. (`{fname}`)")
                await msg.reply("성공적으로 오류 메시지를 전송했어요!")
            else:
                await msg.reply("전송을 취소했어요.")


def setup(bot):
    bot.add_cog(Error(bot))
