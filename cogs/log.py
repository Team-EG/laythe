import discord
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, GuildEmbed, EmbedColor
from module.utils import permission_translates, rtc_region_translates, parse_second, to_readable_bool, verification_level_translates


class Log(commands.Cog, name="로깅"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.attachments:
            [await self.bot.execute_guild_log(message.guild, content="로그 저장용 메시지입니다: "+x.url, delete_after=1) for x in message.attachments]

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        if not before.content and not after.content:
            return
        if after.author.bot:
            return
        embed = AuthorEmbed(after.author,
                            title="메시지 수정",
                            color=EmbedColor.NEUTRAL,
                            timestamp=self.bot.kst)
        embed.add_field(name="기존 내용", value=before.content or "(메시지 내용 없음)", inline=False)
        embed.add_field(name="수정된 내용", value=after.content or "(메시지 내용 없음)", inline=False)
        embed.set_footer(text=f"메시지 ID: {after.id}\n작성자 ID: {after.author.id}")
        await self.bot.execute_guild_log(after.guild, embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        embed = AuthorEmbed(message.author,
                            title="메시지 삭제",
                            color=EmbedColor.NEGATIVE,
                            timestamp=self.bot.kst)
        embed.add_field(name="메시지 내용", value=message.content or "(메시지 내용 없음)", inline=False)
        embed.set_footer(text=f"메시지 ID: {message.id}\n작성자 ID: {message.author.id}")
        if message.attachments:
            files = [x.url for x in message.attachments]
            extra_msg = '\n'.join(files)
            embed.add_field(name="첨부파일", value=f"{len(files)}개", inline=False)
            await self.bot.execute_guild_log(message.guild, content=extra_msg)
        await self.bot.execute_guild_log(message.guild, embed=embed)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        if len(payload.message_ids) == 1:
            return
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        embed = GuildEmbed(guild,
                           title="메시지 대량 삭제",
                           description=channel.mention + f" (`#{channel.name}`)",
                           color=EmbedColor.NEGATIVE,
                           timestamp=self.bot.kst)
        embed.add_field(name="삭제된 메시지 개수", value=str(len(payload.message_ids)), inline=False)
        embed.set_footer(text=f"채널 ID: {payload.channel_id}")
        await self.bot.execute_guild_log(guild, embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = GuildEmbed(channel.guild,
                           title="채널 생성",
                           color=EmbedColor.POSITIVE,
                           timestamp=self.bot.kst)
        embed.add_field(name="채널 이름", value=f"{channel.mention} (`#{channel.name}`)", inline=False)
        embed.set_footer(text=f"채널 ID: {channel.id}")
        await self.bot.execute_guild_log(channel.guild, embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = GuildEmbed(channel.guild,
                           title="채널 삭제",
                           color=EmbedColor.NEGATIVE,
                           timestamp=self.bot.kst)
        embed.add_field(name="채널 이름", value=f"`#{channel.name}`", inline=False)
        embed.set_footer(text=f"채널 ID: {channel.id}")
        await self.bot.execute_guild_log(channel.guild, embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        embed = GuildEmbed(after.guild,
                           title="채널 업데이트",
                           description=after.mention + f" (`#{after.name}`)",
                           color=EmbedColor.NEUTRAL,
                           timestamp=self.bot.kst)

        if before.name != after.name:
            embed.add_field(name="채널 이름", value=f"`{before.name}` -> `{after.name}`", inline=False)
        if before.category != after.category:
            embed.add_field(name="카테고리",
                            value=f"`{before.category.name if before.category else '(없음)'}` -> `{after.category.name if after.category else '(없음)'}`",
                            inline=False)

        if isinstance(before, discord.VoiceChannel) and isinstance(after, discord.VoiceChannel):
            if before.bitrate != after.bitrate:
                embed.add_field(name="비트레이트", value=f"`{before.bitrate}`kbps -> `{after.bitrate}`kbps", inline=False)
            if before.rtc_region != after.rtc_region:
                region_before = rtc_region_translates.get(str(before.rtc_region).replace("-", "_"), before.rtc_region)
                region_after = rtc_region_translates.get(str(after.rtc_region).replace("-", "_"), after.rtc_region)
                embed.add_field(name="음악 채널 리전", value=f"`{region_before}` -> `{region_after}`", inline=False)

        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.slowmode_delay != after.slowmode_delay:
                embed.add_field(name="슬로우모드", value=f"{parse_second(before.slowmode_delay)} -> {parse_second(after.slowmode_delay)}", inline=False)
            if before.nsfw != after.nsfw:
                embed.add_field(name="NSFW 여부", value=f"`{to_readable_bool(before.nsfw)}` -> `{to_readable_bool(after.nsfw)}`", inline=False)

        before_overwrites = dict(before.overwrites)
        after_overwrites = dict(after.overwrites)
        if before_overwrites != after_overwrites:
            for k, v in after_overwrites.items():
                b_o = {n.id: m for n, m in before_overwrites.items()}
                if k.id not in b_o:
                    embed.add_field(name=f"`{k.name}` 역할 권한 새로 추가됨",
                                    value=k.mention + "\n" + (
                                        "부여된 권한 없음" if v.is_empty() else f"`{'`, `'.join([permission_translates.get(p, p) for p, x in v if x])}` 권한 부여됨"),
                                    inline=False)
                elif v != b_o[k.id]:
                    before_perms = {a: b for a, b in b_o[k.id]}
                    any_perms_added = [p for p, x in v if x and x != before_perms[p]]
                    any_perms_removed = [p for p, x in v if not x and x != before_perms[p]]
                    embed.add_field(name=f"`{k.name}` 역할 권한 변경됨",
                                    value=k.mention + ("\n부여된 권한 없음" if v.is_empty() else
                                                       ((
                                                            f"\n`{'`, `'.join([permission_translates.get(p, p) for p in any_perms_added])}` 권한 부여됨"
                                                            if any_perms_added else "") +
                                                        (
                                                            f"\n`{'`, `'.join([permission_translates.get(p, p) for p in any_perms_removed])}` 권한 제거됨"
                                                            if any_perms_removed else ""))),
                                    inline=False)
            for k, v in before_overwrites.items():
                if k.id not in [x.id for x in after_overwrites.keys()]:
                    embed.add_field(name=f"`{k.name}` 역할 권한 제거됨",
                                    value=k.mention,
                                    inline=False)

        embed.set_footer(text=f"채널 ID: {after.id}")

        if not embed.fields:
            return

        if before.position != after.position:  # Prevent spam
            embed.add_field(name="채널 위치", value=f"`{before.position}`번째 -> `{after.position}`번째", inline=False)

        await self.bot.execute_guild_log(after.guild, embed=embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        embed = GuildEmbed(after,
                           title="서버 업데이트",
                           color=EmbedColor.NEUTRAL,
                           timestamp=self.bot.kst)
        if before.name != after.name:
            embed.add_field(name="서버 이름", value=f"`{before.name}` -> `{after.name}`")
        if before.region != after.region:
            region_before = rtc_region_translates.get(str(before.region).replace("-", "_"), before.region)
            region_after = rtc_region_translates.get(str(after.region).replace("-", "_"), after.region)
            embed.add_field(name="서버 리전", value=f"`{region_before}` -> `{region_after}`", inline=False)
        if before.verification_level != after.verification_level:
            verification_level_before = verification_level_translates.get(str(before.verification_level).replace("-", "_"), before.verification_level)
            verification_level_after = verification_level_translates.get(str(after.verification_level).replace("-", "_"), after.verification_level)
            embed.add_field(name="보안 수준", value=f"`{verification_level_before}` -> `{verification_level_after}`", inline=False)
        if before.owner != after.owner:
            embed.add_field(name="서버 소유자", value=f"{before.owner.mention} -> {after.owner.mention}\n(`{before.owner}` -> `{after.owner}`)", inline=False)
        if before.system_channel != after.system_channel:
            if before.system_channel is None:
                before_sys = "`(없음)`"
            else:
                before_sys = before.system_channel.mention
            if after.system_channel is None:
                after_sys = "`(없음)`"
            else:
                after_sys = after.system_channel.mention
            embed.add_field(name="시스템 메시지 채널", value=f"{before_sys} -> {after_sys}", inline=False)
        if before.premium_tier != after.premium_tier:
            embed.add_field(name="니트로 부스트 레벨", value=f"{before.premium_tier}레벨 -> {after.premium_tier}레벨", inline=False)
        if before.premium_subscription_count != after.premium_subscription_count:
            embed.add_field(name="니트로 부스트 수", value=f"{before.premium_subscription_count}개 -> {after.premium_subscription_count}개", inline=False)
        embed.set_footer(text=f"서버 ID: {after.id}")
        if not embed.fields:
            return
        await self.bot.execute_guild_log(after, embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        embed = GuildEmbed(role.guild, title="역할 생성", color=EmbedColor.POSITIVE, timestamp=self.bot.kst)
        embed.add_field(name="역할", value=f"{role.mention} (`@{role.name}`)", inline=False)
        embed.set_footer(text=f"역할 ID: {role.id}")
        await self.bot.execute_guild_log(role.guild, embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        embed = GuildEmbed(role.guild, title="역할 삭제", color=EmbedColor.NEGATIVE, timestamp=self.bot.kst)
        embed.add_field(name="역할", value=f"`@{role.name}`", inline=False)
        embed.set_footer(text=f"역할 ID: {role.id}")
        await self.bot.execute_guild_log(role.guild, embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        embed = GuildEmbed(after.guild, title=f"역할 업데이트", description=after.mention + f" (`@{after.name}`)", color=EmbedColor.NEUTRAL, timestamp=self.bot.kst)

        if before.name != after.name:
            embed.add_field(name="이름", value=f"`{before.name}` -> `{after.name}`", inline=False)
        if before.color != after.color:
            embed.add_field(name="색상", value=f"{before.color} -> {after.color}", inline=False)
        if before.position != after.position:
            embed.add_field(name="위치", value=f"`{before.position}`번째 -> `{after.position}`번째", inline=False)

        before_perms = dict(before.permissions)
        after_perms = dict(after.permissions)
        if before_perms != after_perms:
            embed.add_field(name="권한",
                            value='\n'.join([f"`{permission_translates.get(k, k)}`: {to_readable_bool(v)} -> {to_readable_bool(after_perms[k])}"
                                             for k, v in before_perms.items() if v != after_perms[k]]),
                            inline=False)
        embed.set_footer(text=f"역할 ID: {after.id}")
        if not embed.fields:
            return
        await self.bot.execute_guild_log(after.guild, embed=embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        embed = GuildEmbed(guild, title="서버 이모지 업데이트", colour=EmbedColor.NEUTRAL, timestamp=self.bot.kst)
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        deleted = [x for x in before if x not in after]
        if deleted:
            embed.add_field(name="제거된 이모지", value=', '.join([f"`{x.name}`" for x in deleted]), inline=False)
        added = [x for x in after if x not in before]
        if added:
            embed.add_field(name="추가된 이모지", value=', '.join([f"{x.mention} (`{x.name}`)" for x in added]), inline=False)
        if not embed.fields:
            return
        await self.bot.execute_guild_log(guild, embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = GuildEmbed(guild, title="멤버 차단 해제", description=user, colour=EmbedColor.POSITIVE, timestamp=self.bot.kst)
        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(text=f"유저 ID: {user.id}")
        await self.bot.execute_guild_log(guild, embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = GuildEmbed(guild, title="멤버 차단", description=user, colour=EmbedColor.NEGATIVE, timestamp=self.bot.kst)
        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(text=f"유저 ID: {user.id}")
        await self.bot.execute_guild_log(guild, embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        embed = GuildEmbed(after.guild, title="멤버 정보 업데이트", description=after.mention + f" ({after})", colour=EmbedColor.NEUTRAL, timestamp=self.bot.kst)
        if before.display_name != after.display_name:
            embed.add_field(name="닉네임", value=f"{before.display_name} -> {after.display_name}", inline=False)
        if before.roles != after.roles:
            deleted = [x for x in before.roles if x not in after.roles]
            added = [x for x in after.roles if x not in before.roles]
            if added:
                embed.add_field(name="추가된 역할", value=', '.join([x.mention for x in added]), inline=False)
            if deleted:
                embed.add_field(name="제거된 역할", value=', '.join([x.mention for x in deleted]), inline=False)
        if not embed.fields:
            return
        embed.set_footer(text=f"유저 ID: {after.id}")
        await self.bot.execute_guild_log(after.guild, embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = GuildEmbed(member.guild, title="새로운 멤버", description=member.mention + f" ({member})", colour=EmbedColor.POSITIVE, timestamp=self.bot.kst)
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f"유저 ID: {member.id}")
        await self.bot.execute_guild_log(member.guild, embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = GuildEmbed(member.guild, title="멤버 퇴장", description=member, colour=EmbedColor.NEGATIVE, timestamp=self.bot.kst)
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f"유저 ID: {member.id}")
        await self.bot.execute_guild_log(member.guild, embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        try:
            msg = channel.get_partial_message(payload.message_id) or await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        embed = GuildEmbed(guild,
                           title="모든 반응 제거",
                           description=f"[해당 메시지로 바로가기]({msg.jump_url})",
                           color=EmbedColor.NEGATIVE,
                           timestamp=self.bot.kst)
        embed.set_footer(text=f"메시지 ID: {payload.message_id}")
        await self.bot.execute_guild_log(guild, embed=embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        embed = GuildEmbed(invite.guild, title="새 초대코드 생성", colour=EmbedColor.POSITIVE, timestamp=self.bot.kst)
        embed.add_field(name="초대코드를 생성한 멤버", value=invite.inviter.mention + f" (`{invite.inviter}`)", inline=False)
        embed.add_field(name="초대코드", value=invite.url)
        embed.set_footer(text=f"멤버 ID: {invite.inviter.id}")
        await self.bot.execute_guild_log(invite.guild, embed=embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        embed = GuildEmbed(invite.guild, title="초대코드 삭제", colour=EmbedColor.NEGATIVE, timestamp=self.bot.kst)
        embed.add_field(name="삭제된 초대코드", value=invite.url)
        await self.bot.execute_guild_log(invite.guild, embed=embed)


def setup(bot):
    bot.add_cog(Log(bot))
