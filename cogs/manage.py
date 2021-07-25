import typing

import discord
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, Pager


class Manage(commands.Cog, name="관리"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.group(name="정리", description="메세지를 대량으로 삭제해요.", aliases=["purge"], usage="`{prefix}정리 도움` 명령어를 참고해주세요.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, count: typing.Optional[int] = None):
        if count is not None and not ctx.invoked_subcommand:
            if count < 1 or count > 100:
                return await ctx.reply("❌ 삭제할 메세지 개수는 1 이상, 100 이하만 가능해요.")
            await ctx.message.delete()
            await ctx.channel.purge(limit=count)
            await ctx.send(f"✅ 메세지 {count}개를 정리했어요.\n`이 메세지는 5초 후 삭제돼요.`", delete_after=5)

    @purge.command(name="도움")
    async def purge_help(self, ctx: commands.Context):
        embed = AuthorEmbed(ctx.author,
                            title="정리 명령어 도움말",
                            timestamp=ctx.message.created_at,
                            color=EmbedColor.DEFAULT,
                            display_footer=True)
        embed.add_field(name=f"{ctx.prefix}정리 [개수:숫자]", value="개수 만큼의 메세지를 삭제해요.", inline=False)
        embed.add_field(name=f"{ctx.prefix}정리 메세지 [메세지:메세지 ID 또는 메세지 링크]", value="해당 메세지 까지의 모든 메세지를 삭제해요.", inline=False)
        embed.add_field(name=f"{ctx.prefix}정리 유저 [유저:유저 ID 또는 맨션] [탐색 범위:숫자]", value="선택한 유저가 보낸 메세지들을 제한 범위까지 탐색 후 삭제해요.", inline=False)
        await ctx.reply(embed=embed)

    @purge.command(name="메세지", alias=["메시지"])
    async def purge_message(self, ctx: commands.Context, message: discord.Message):
        tgt_list = [message]
        async for m in ctx.channel.history(after=message):
            tgt_list.append(m)
        await ctx.channel.delete_messages(tgt_list)
        await ctx.send(f"✅ 선택한 메세지부터 {len(tgt_list)}개의 메세지를 정리했어요.\n`이 메세지는 5초 후 삭제돼요.`", delete_after=5)

    @purge.command(name="유저")
    async def purge_user(self, ctx: commands.Context, user: discord.Member, limit: int):
        if limit > 100:
            return await ctx.send("❌ 오류 방지를 위해 검색되는 메시지의 최대 범위는 100개로 제한돼요.")
        tgt_list = []
        async for message in ctx.channel.history(limit=limit):
            if message.author == user:
                tgt_list.append(message)
        await ctx.channel.delete_messages(tgt_list)
        await ctx.send(f"✅ 선택한 유저가 전송한 {len(tgt_list)}개의 메세지를 정리했어요.\n`이 메세지는 5초 후 삭제돼요.`", delete_after=5)

    @commands.command(name="추방", description="선택한 유저를 서버에서 추방해요.", usage="`{prefix}추방 [유저:유저 ID 또는 맨션] (사유:문장)`", aliases=["kick"])
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_member(self, ctx: commands.Context, user: discord.Member, reason: str = None):
        try:
            await user.send(f"`{user.guild.name}`에서 추방되었어요.\n사유: {reason or '없음'}")
        except (discord.Forbidden, discord.HTTPException):
            await ctx.reply("ℹ 이런! DM으로 추방 사유를 보내지 못했어요. 사유 메세지를 전송하지 않고 바로 추방할께요.")
        await user.kick(reason=reason)
        await ctx.reply("✅ 성공적으로 해당 유저를 추방했어요.")

    @commands.command(name="차단", description="선택한 유저를 서버에서 차단해요.", usage="`{prefix}차단 [유저:유저 ID 또는 맨션] (사유:문장)`", aliases=["ban"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_member(self, ctx: commands.Context, user: discord.Member, reason: str = None):
        try:
            await user.send(f"`{user.guild.name}`에서 차단되었어요.\n사유: {reason or '없음'}")
        except (discord.Forbidden, discord.HTTPException):
            await ctx.reply("ℹ 이런! DM으로 차단 사유를 보내지 못했어요. 사유 메세지를 전송하지 않고 바로 차단할께요.")
        await user.ban(reason=reason)
        await ctx.reply("✅ 성공적으로 해당 유저를 차단했어요.")


def setup(bot):
    bot.add_cog(Manage(bot))
