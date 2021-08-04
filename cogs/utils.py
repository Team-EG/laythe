import datetime
import platform
import discord
import discord_slash
import psutil
from discord.ext import commands
from discord_slash.utils import manage_components
from module import LaytheClient, AuthorEmbed, EmbedColor, utils, GuildEmbed
from module.utils import rtc_region_translates, verification_level_translates, verification_desc_translates


class Utils(commands.Cog, name="유틸리티"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.command(name="맞춤법", description="맞춤법을 검사해줘요. 틀린 경우가 있으니 참고용으로만 사용해주세요.", usage="`{prefix}맞춤법 [문장:문자열]`")
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

    @commands.command(name="유저정보", description="유저의 정보를 알려줘요.", usage="`{prefix}유저정보 (유저:맨션 또는 ID:명령어를 사용한 유저)`")
    async def user_info(self, ctx: commands.Context, user: discord.Member = None):
        user = user or ctx.author
        join_time = int(user.joined_at.timestamp())
        embed = AuthorEmbed(user, title=f"유저 정보", color=EmbedColor.DEFAULT, timestamp=ctx.message.created_at)
        embed.add_field(name="유저네임", value=f"{str(user)}", inline=False)
        embed.add_field(name="ID", value=f"{user.id}", inline=False)
        embed.add_field(name="계정 생성일", value=f"<t:{int(user.created_at.timestamp())}>", inline=False)
        embed.add_field(name=f"이 서버에 들어온 시간", value=f"<t:{join_time}> (<t:{join_time}:R>)", inline=False)
        embed.add_field(name="최고 역할", value=user.top_role.mention, inline=False)
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.reply(embed=embed)

    @commands.command(name="서버정보", description="서버의 정보를 알려줘요.")
    async def server_info(self, ctx: commands.Context):
        region = rtc_region_translates.get(str(ctx.guild.region).replace("-", "_"), ctx.guild.region)
        verify_lvl = verification_level_translates.get(str(ctx.guild.verification_level).replace("-", "_"), ctx.guild.verification_level)
        verify_desc = verification_desc_translates.get(str(ctx.guild.verification_level).replace("-", "_"), ctx.guild.verification_level)
        embed = GuildEmbed(ctx.guild, title="서버 정보", color=EmbedColor.DEFAULT)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name="소유자", value=ctx.guild.owner.mention, inline=False)
        embed.add_field(name="유저 수", value=f"`{ctx.guild.member_count}`명", inline=False)
        embed.add_field(name="서버 생성일", value=f"<t:{int(ctx.guild.created_at.timestamp())}>", inline=False)
        embed.add_field(name="채널 수",
                        value=f"채팅 채널 `{len(ctx.guild.text_channels)}`개\n"
                              f"음성 채널 `{len(ctx.guild.voice_channels)}`개\n"
                              f"카테고리 `{len(ctx.guild.categories)}`개",
                        inline=False)
        embed.add_field(name="서버 부스트 레벨", value=f"`{ctx.guild.premium_tier}`레벨", inline=False)
        embed.add_field(name="서버 부스트 수", value=f"`{ctx.guild.premium_subscription_count}`개 (부스터 `{len(ctx.guild.premium_subscribers)}`명)", inline=False)
        embed.add_field(name="역할 수", value=f"`{len(ctx.guild.roles)}`개", inline=False)
        embed.add_field(name="서버 최고 역할", value=ctx.guild.roles[-1].mention, inline=False)
        embed.add_field(name="서버 위치", value=f"`{region}`", inline=False)
        embed.add_field(name="서버 보안 수준", value=f"`{verify_lvl}`\n{verify_desc}", inline=False)
        embed.set_image(url=ctx.guild.banner_url)
        await ctx.send(embed=embed)

    @commands.command(name="정보", description="레이테의 정보를 알려줘요")
    async def laythe_info(self, ctx: commands.Context):
        guild_count = len(self.bot.guilds)
        user_count = len(list(self.bot.get_all_members()))
        process = psutil.Process()
        uptime_sys = (datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())).total_seconds()
        uptime_bot = (datetime.datetime.now() - datetime.datetime.fromtimestamp(process.create_time())).total_seconds()
        memory = psutil.virtual_memory()
        node = self.bot.lavalink.node_manager.nodes[0].stats
        embed = AuthorEmbed(ctx.author,
                            title="레이테 정보",
                            description="Developed and maintained by [Team EG](https://discord.gg/gqJBhar).",
                            color=EmbedColor.DEFAULT,
                            timestamp=ctx.message.created_at)
        embed.add_field(name="서버 수", value=f"`{guild_count}`개", inline=False)
        embed.add_field(name="유저 수", value=f"`{user_count}`명", inline=False)
        embed.add_field(name="라이브러리 버전",
                        value=f"<:python:815496209682006036> Python `{platform.python_version()}` | "
                              f"<:dpy2:815496751452651540> discord.py `{discord.__version__}` | "
                              f"<:din:865108330750017547> discord-py-interactions `{discord_slash.__version__}`\n",
                        inline=False)
        embed.add_field(name="업타임", value=f"서버: `{utils.parse_second(round(uptime_sys))}` | 봇: `{utils.parse_second(round(uptime_bot))}`", inline=False)
        embed.add_field(name="레이테 서버 정보", value=f"CPU `{psutil.cpu_percent()}`% 사용중\n램 `{memory.percent}`% 사용중", inline=False)
        embed.add_field(name="Lavalink 정보",
                        value=f"총 `{node.players}`개 노드 (`{node.playing_players}`개 노드에서 재생중)\n노드 부하: `{round(node.lavalink_load*100)}`%",
                        inline=False)
        github_emoji = self.bot.get_emoji(872322613987389441)
        team_eg = manage_components.create_button(style=5, label="Team EG Web", url="https://team-eg.github.io/")
        github = manage_components.create_button(style=5, label="GitHub", emoji=github_emoji, url="https://github.com/Team-EG/laythe")
        row = manage_components.create_actionrow(team_eg, github)
        await ctx.reply(embed=embed, components=[row])


def setup(bot):
    bot.add_cog(Utils(bot))
