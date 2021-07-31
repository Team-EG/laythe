import datetime
import platform
import discord
import discord_slash
import psutil
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, utils


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
        embed = discord.Embed(title=f"`{user.display_name}`님의 정보", color=EmbedColor.DEFAULT, timestamp=ctx.message.created_at)
        embed.add_field(name="유저네임", value=f"{str(user)}", inline=False)
        embed.add_field(name="ID", value=f"{user.id}", inline=False)
        embed.add_field(name=f"이 서버에 들어온 시간", value=f"<t:{join_time}> (<t:{join_time}:R>)", inline=False)
        embed.add_field(name="최고 역할", value=user.top_role.mention, inline=False)
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.reply(embed=embed)

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
        embed.add_field(name="서버 수", value=f"{guild_count}개", inline=False)
        embed.add_field(name="유저 수", value=f"{user_count}명", inline=False)
        embed.add_field(name="라이브러리 버전",
                        value=f"<:python:815496209682006036> Python `{platform.python_version()}` | "
                              f"<:dpy2:815496751452651540> discord.py `{discord.__version__}` | "
                              f"<:din:865108330750017547> discord-py-interactions `{discord_slash.__version__}`\n",
                        inline=False)
        embed.add_field(name="업타임", value=f"서버: {utils.parse_second(round(uptime_sys))} | 봇: {utils.parse_second(round(uptime_bot))}", inline=False)
        embed.add_field(name="레이테 서버 정보", value=f"CPU `{psutil.cpu_percent()}`% 사용중\n램 `{memory.percent}`% 사용중", inline=False)
        embed.add_field(name="Lavalink 정보",
                        value=f"총 `{node.players}`개 노드 (`{node.playing_players}`개 노드에서 재생중)\n노드 부하: `{round(node.lavalink_load*100)}`%",
                        inline=False)
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Utils(bot))
