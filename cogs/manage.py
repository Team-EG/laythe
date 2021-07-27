import datetime
import typing
import discord
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, Pager, GuildEmbed, Cursor


class Manage(commands.Cog, name="관리"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.group(name="정리", description="메시지를 대량으로 삭제해요.", aliases=["purge"], usage="`{prefix}정리 도움` 명령어를 참고해주세요.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, count: typing.Optional[int] = None):
        if count is not None and not ctx.invoked_subcommand:
            if count < 1 or count > 100:
                return await ctx.reply("❌ 삭제할 메시지 개수는 1 이상, 100 이하만 가능해요.")
            await ctx.message.delete()
            await ctx.channel.purge(limit=count)
            await ctx.send(f"✅ 메시지 {count}개를 정리했어요.\n`이 메시지는 5초 후 삭제돼요.`", delete_after=5)

    @purge.command(name="도움")
    async def purge_help(self, ctx: commands.Context):
        embed = AuthorEmbed(ctx.author,
                            title="정리 명령어 도움말",
                            timestamp=ctx.message.created_at,
                            color=EmbedColor.DEFAULT,
                            display_footer=True)
        embed.add_field(name=f"{ctx.prefix}정리 [개수:숫자]", value="개수 만큼의 메시지를 삭제해요.", inline=False)
        embed.add_field(name=f"{ctx.prefix}정리 메시지 [메시지:메시지 ID 또는 메시지 링크]", value="해당 메시지 까지의 모든 메시지를 삭제해요.", inline=False)
        embed.add_field(name=f"{ctx.prefix}정리 유저 [유저:유저 ID 또는 맨션] [탐색 범위:숫자]", value="선택한 유저가 보낸 메시지들을 제한 범위까지 탐색 후 삭제해요.", inline=False)
        await ctx.reply(embed=embed)

    @purge.command(name="메시지", alias=["메시지"])
    async def purge_message(self, ctx: commands.Context, message: discord.Message):
        tgt_list = [message]
        async for m in ctx.channel.history(after=message):
            tgt_list.append(m)
        await ctx.channel.delete_messages(tgt_list)
        await ctx.send(f"✅ 선택한 메시지부터 {len(tgt_list)}개의 메시지를 정리했어요.\n`이 메시지는 5초 후 삭제돼요.`", delete_after=5)

    @purge.command(name="유저")
    async def purge_user(self, ctx: commands.Context, user: discord.Member, limit: int):
        if limit > 100:
            return await ctx.send("❌ 오류 방지를 위해 검색되는 메시지의 최대 범위는 100개로 제한돼요.")
        tgt_list = []
        async for message in ctx.channel.history(limit=limit):
            if message.author == user:
                tgt_list.append(message)
        await ctx.channel.delete_messages(tgt_list)
        await ctx.send(f"✅ 선택한 유저가 전송한 {len(tgt_list)}개의 메시지를 정리했어요.\n`이 메시지는 5초 후 삭제돼요.`", delete_after=5)

    @commands.command(name="뮤트",
                      description="선택한 유저를 뮤트해요. 뮤트 역할을 먼저 등록해야 사용이 가능해요.",
                      usage="`{prefix}뮤트 [유저:유저 ID 또는 맨션] (사유:문장:없음)`",
                      aliases=["음소거", "mute"])
    @commands.has_permissions(manage_roles=True, manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute_user(self, ctx: commands.Context, user: discord.Member, *, reason: str = None):
        setting = await self.bot.cache_manager.get_settings(ctx.guild.id, "mute_role")
        mute_role = setting[0]["mute_role"]
        if not mute_role:
            return await ctx.reply("❌ 먼저 뮤트 역할을 설정에서 등록해주세요.")
        mute_role = ctx.guild.get_role(mute_role)
        if mute_role.id in map(lambda x: x.id, user.roles):
            return await ctx.reply("❌ 이미 뮤트된 유저에요.")
        await user.add_roles(mute_role, reason=reason)
        await ctx.reply("✅ 성공적으로 해당 유저를 뮤트했어요.")

    @commands.command(name="언뮤트",
                      description="선택한 유저를 언뮤트해요. 뮤트 역할을 먼저 등록해야 사용이 가능해요.",
                      usage="`{prefix}언뮤트 [유저:유저 ID 또는 맨션] (사유:문장:없음)`",
                      aliases=["unmute"])
    @commands.has_permissions(manage_roles=True, manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute_user(self, ctx: commands.Context, user: discord.Member, *, reason: str = None):
        setting = await self.bot.cache_manager.get_settings(ctx.guild.id, "mute_role")
        mute_role = setting[0]["mute_role"]
        if not mute_role:
            return await ctx.reply("❌ 먼저 뮤트 역할을 설정에서 등록해주세요.")
        mute_role = ctx.guild.get_role(mute_role)
        if mute_role.id not in map(lambda x: x.id, user.roles):
            return await ctx.reply("❌ 뮤트되지 않은 유저에요.")
        await user.remove_roles(mute_role, reason=reason)
        await ctx.reply("✅ 성공적으로 해당 유저를 언뮤트했어요.")

    @commands.group(name="경고", description="경고 관련 명령어에요.", usage="`{prefix}경고` 명령어를 참고해주세요.")
    async def warn_user(self, ctx: commands.Context):
        if ctx.invoked_subcommand:
            return
        embed = AuthorEmbed(ctx.author, title="경고 명령어 도움말", color=EmbedColor.DEFAULT)
        embed.add_field(name=f"{ctx.prefix}경고 추가 [유저:유저 ID 또는 맨션] (사유:문장:없음)", value="선택한 유저에게 경고를 부여해요.", inline=False)
        embed.add_field(name=f"{ctx.prefix}경고 삭제 [유저:유저 ID 또는 맨션] [경고 ID:숫자(경고 ID)]", value="선택한 경고를 삭제해요.", inline=False)
        embed.add_field(name=f"{ctx.prefix}경고 목록 (유저:유저 ID 또는 맨션:명령어 사용자)", value="선택한 유저의 경고 목록을 보여줘요.", inline=False)
        # embed.add_field(name=f"{ctx.prefix}경고 보기 [유저:유저 ID 또는 맨션] [경고 ID:숫자(경고 ID)]", value="선택한 경고를 보여줘요.", inline=False)
        await ctx.reply(embed=embed)

    @warn_user.command(name="추가")
    @commands.has_permissions(ban_members=True)
    async def warn_user_add(self, ctx: commands.Context, user: discord.Member, *, reason: str = None):
        now = round(ctx.message.created_at.timestamp())
        reason = reason or "없음"
        await self.bot.db.execute("""INSERT INTO warns VALUES (%s, %s, %s, %s, %s)""", (ctx.guild.id, now, user.id, ctx.author.id, reason))
        embed = GuildEmbed(ctx.guild, title=f"유저 경고 추가", timestamp=ctx.message.created_at, color=EmbedColor.NEGATIVE)
        embed.add_field(name="경고 대상", value=f"{user.mention} (`{user}` (ID: `{user.id}`))", inline=False)
        embed.add_field(name="경고를 추가한 관리자", value=f"{ctx.author.mention} (`{ctx.author}` (ID: `{ctx.author.id}`))", inline=False)
        embed.add_field(name="경고 ID", value=f"`{now}`", inline=False)
        embed.add_field(name="경고 사유", value=reason, inline=False)
        await self.bot.execute_guild_log(ctx.guild, embed=embed)
        await ctx.reply("✅ 성공적으로 경고를 추가했어요. 자세한 내용은 다음을 참고해주세요.", embed=embed)

    @warn_user.command(name="삭제")
    @commands.has_permissions(ban_members=True)
    async def warn_user_remove(self, ctx: commands.Context, user: discord.Member, warn_id: int):
        await self.bot.db.execute("""DELETE FROM warns WHERE guild_id=%s AND user_id=%s AND date=%s""", (ctx.guild.id, user.id, warn_id))
        await ctx.reply("✅ 해당 경고를 삭제했어요. 경고 삭제 명령어의 작동 특성으로 잘못된 경고 ID일 경우에도 해당 메시지가 전송되지만 경고가 삭제되지 않으므로 주의하세요.")

    @warn_user.command(name="목록")
    async def warn_user_list(self, ctx: commands.Context, user: discord.Member = None):
        user = user or ctx.author
        warns = await self.bot.db.fetch("""SELECT * FROM warns WHERE guild_id=%s AND user_id=%s""", (ctx.guild.id, user.id))
        if not warns:
            return await ctx.reply("ℹ 해당 유저의 경고 기록이 존재하지 않아요.")
        embed = AuthorEmbed(user, title=f"경고 목록 - 총 {len(warns)}개", color=EmbedColor.NEGATIVE, timestamp=ctx.message.created_at)
        cursor = Cursor(self.bot, ctx.message, [f"경고 ID: `{x['date']}`" for x in warns], embed)
        _msg, resp = await cursor.start()
        if resp is None:
            return await _msg.delete()
        warn = warns[resp]
        moderator = ctx.guild.get_member(warn["mod_id"]) or self.bot.get_user(warn["mod_id"])
        resp = AuthorEmbed(user, title=f"경고 정보 - #{warn['date']}", color=EmbedColor.NEGATIVE, timestamp=datetime.datetime.fromtimestamp(warn['date']))
        resp.add_field(name="경고 대상", value=f"{user.mention} (`{user}` (ID: `{user.id}`))", inline=False)
        resp.add_field(name="경고를 추가한 관리자",
                       value=f"{moderator.mention} (`{moderator}` (ID: `{moderator.id}`))" if moderator else f"⚠ 관리자를 못 찾았어요. (관리자 ID: {warn['mod_id']})",
                       inline=False)
        resp.add_field(name="경고 ID", value=f"`{warn['date']}`", inline=False)
        resp.add_field(name="경고 사유", value=warn['reason'], inline=False)
        await _msg.edit(embed=resp, components=[])

    @commands.command(name="추방", description="선택한 유저를 서버에서 추방해요.", usage="`{prefix}추방 [유저:유저 ID 또는 맨션] (사유:문장:없음)`", aliases=["kick"])
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_member(self, ctx: commands.Context, user: discord.Member, *, reason: str = None):
        try:
            await user.send(f"`{user.guild.name}`에서 추방되었어요.\n사유: {reason or '없음'}")
        except (discord.Forbidden, discord.HTTPException):
            await ctx.reply("ℹ 이런! DM으로 추방 사유를 보내지 못했어요. 사유 메시지를 전송하지 않고 바로 추방할께요.")
        await user.kick(reason=reason)
        await ctx.reply("✅ 성공적으로 해당 유저를 추방했어요.")

    @commands.command(name="차단", description="선택한 유저를 서버에서 차단해요.", usage="`{prefix}차단 [유저:유저 ID 또는 맨션] (사유:문장:없음)`", aliases=["ban"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_member(self, ctx: commands.Context, user: discord.Member, *, reason: str = None):
        try:
            await user.send(f"`{user.guild.name}`에서 차단되었어요.\n사유: {reason or '없음'}")
        except (discord.Forbidden, discord.HTTPException):
            await ctx.reply("ℹ 이런! DM으로 차단 사유를 보내지 못했어요. 사유 메시지를 전송하지 않고 바로 차단할께요.")
        await user.ban(reason=reason)
        await ctx.reply("✅ 성공적으로 해당 유저를 차단했어요.")


def setup(bot):
    bot.add_cog(Manage(bot))
