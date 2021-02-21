import time
from discord.ext import commands
from module import AuthorEmbed, EmbedColor
from module import JBotClient


class Basic(commands.Cog):
    def __init__(self, bot: JBotClient):
        self.bot = bot

    @commands.command(name="ping", description="봇의 레이턴시를 알려줍니다.", aliases=["핑", "퐁", "pong"])
    async def ping(self, ctx: commands.Context):
        send_start = time.time()
        msg = await ctx.send("잠시만 기다려주세요... (1)")
        send_end = time.time()
        send_latency = send_end - send_start
        edit_start = time.time()
        await msg.edit(content="잠시만 기다려주세요... (2)")
        edit_end = time.time()
        edit_latency = edit_end - edit_start
        delete_start = time.time()
        await msg.delete()
        delete_end = time.time()
        delete_latency = delete_end - delete_start
        embed = AuthorEmbed(ctx.author,
                            title="🏓 퐁!",
                            timestamp=ctx.message.created_at,
                            color=EmbedColor.DEFAULT,
                            display_footer=True)
        embed.description = f"디스코드 웹소켓 레이턴시: {round(self.bot.latency*1000)}ms\n" \
                            f"메시지 전송 레이턴시: {round(send_latency*1000)}ms\n" \
                            f"메시지 수정 레이턴시: {round(edit_latency*1000)}ms\n" \
                            f"메시지 삭제 레이턴시: {round(delete_latency*1000)}ms"
        """
        embed.add_field(name="디스코드 웹소켓 레이턴시", value=f"{round(self.bot.latency*1000)}ms")
        embed.add_field(name="메시지 전송 레이턴시", value=f"{round(send_latency*1000)}ms")
        embed.add_field(name="메시지 수정 레이턴시", value=f"{round(edit_latency*1000)}ms")
        embed.add_field(name="메시지 삭제 레이턴시", value=f"{round(delete_latency*1000)}ms")
        """
        await ctx.reply(embed=embed)

    @commands.command(name="raise")
    async def _raise(self, ctx):
        await ctx.reply([][2])


def setup(bot):
    bot.add_cog(Basic(bot))
