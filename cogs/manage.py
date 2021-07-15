import typing
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, Pager


class Manage(commands.Cog):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.group(name="정리", description="메세지를 대량으로 삭제해요.", aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, count: typing.Optional[int] = None):
        if count is not None and not ctx.invoked_subcommand:
            if count < 1 or count > 100:
                return await ctx.reply("삭제할 메세지 개수는 1 이상, 100 이하만 가능해요.")
            await ctx.message.delete()
            await ctx.channel.purge(limit=count)
            msg = await ctx.send(f"메세지 {count}개를 정리했어요.\n`이 메세지는 5초 후 삭제돼요.`")
            await msg.delete(delay=5)


def setup(bot):
    bot.add_cog(Manage(bot))
