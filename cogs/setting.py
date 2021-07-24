from discord.ext import commands
from module import LaytheClient, GuildEmbed, EmbedColor, Pager, LaytheSettingFlags
from module.utils import to_setting_flags, to_readable_bool


class Setting(commands.Cog, name="봇 설정"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.group(name="설정", description="이 서버에서의 레이테 설정을 보거나 수정할 수 있어요.", usage="`{prefix} 설정 도움` 명령어를 참고해주세요.")
    @commands.has_permissions(administrator=True)
    async def laythe_setting(self, ctx: commands.Context):
        if ctx.invoked_subcommand:
            return
        settings = await self.bot.cache_manager.get_settings(ctx.guild.id)
        if not settings:
            return await ctx.reply("이런! 아직 레이테 설정을 사용할 수 없는 것 같아요... 최대 5분정도 기다린 뒤에 재시도해주세요.")
        settings = settings[0]
        flags = to_setting_flags(settings["flags"])
        embed = GuildEmbed(ctx.guild, title="Laythe 설정 정보", color=EmbedColor.DEFAULT, timestamp=ctx.message.created_at)
        embed.add_field(name="커스텀 프리픽스", value=settings["custom_prefix"] or "(없음)")
        embed.add_field(name="레벨 기능을 사용하나요?", value=to_readable_bool(LaytheSettingFlags.USE_LEVEL in flags))
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Setting(bot))
