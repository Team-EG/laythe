import discord
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, GuildEmbed, EmbedColor
from module.utils import permission_translates, rtc_region_translates, parse_second, to_readable_bool


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
        if before.position != after.position:
            embed.add_field(name="채널 위치", value=f"`{before.position}`번째 -> `{after.position}`번째", inline=False)

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
        for k, v in after_overwrites.items():
            b_o = {n.id: m for n, m in before_overwrites.items()}
            if k.id not in b_o:
                embed.add_field(name=f"`{k.name}` 역할 권한 새로 추가됨",
                                value=k.mention+"\n"+("부여된 권한 없음" if v.is_empty() else f"`{'`, `'.join([permission_translates.get(p, p) for p, x in v if x])}` 권한 부여됨"),
                                inline=False)
            elif v != b_o[k.id]:
                before_perms = {a: b for a, b in b_o[k.id]}
                any_perms_added = [p for p, x in v if x and x != before_perms[p]]
                any_perms_removed = [p for p, x in v if not x and x != before_perms[p]]
                embed.add_field(name=f"`{k.name}` 역할 권한 변경됨",
                                value=k.mention + ("\n부여된 권한 없음" if v.is_empty() else
                                                   ((f"\n`{'`, `'.join([permission_translates.get(p, p) for p in any_perms_added])}` 권한 부여됨"
                                                     if any_perms_added else "") +
                                                    (f"\n`{'`, `'.join([permission_translates.get(p, p) for p in any_perms_removed])}` 권한 제거됨"
                                                     if any_perms_removed else ""))),
                                inline=False)
        for k, v in before_overwrites.items():
            if k.id not in [x.id for x in after_overwrites.keys()]:
                embed.add_field(name=f"`{k.name}` 역할 권한 제거됨",
                                value=k.mention,
                                inline=False)

        if not embed.fields:
            return

        await self.bot.execute_guild_log(after.guild, embed=embed)


def setup(bot):
    bot.add_cog(Log(bot))
