from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor


class Utils(commands.Cog):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.command(name="맞춤법", description="맞춤법을 검사해줘요. 틀린 경우가 있으니 참고용으로만 사용해주세요.")
    async def spell_check(self, ctx: commands.Context, *, text):
        orig = text
        changed = text
        resp = await self.bot.spell.parse_async(text)
        if resp is None:
            return await ctx.reply("맞춤법 오류가 없어요.")
        for x in resp["errInfo"]:
            orig_text = x["orgStr"]
            changed_text = x["candWord"]
            changed = changed.replace(orig_text, changed_text)
        if changed == orig:
            return await ctx.reply("맞춤법 오류가 없어요.")
        for x in resp["errInfo"]:
            orig_text = x["orgStr"]
            orig = orig.replace(orig_text, f"[__{orig_text}__]")
        embed = AuthorEmbed(ctx.author,
                            title="문법 오류를 발견했어요.",
                            timestamp=ctx.message.created_at,
                            color=EmbedColor.NEGATIVE,
                            display_footer=True)
        embed.add_field(name="수정 전", value=orig, inline=False)
        embed.add_field(name="수정 후", value=changed, inline=False)
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Utils(bot))
