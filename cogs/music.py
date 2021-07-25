import discord
import lavalink
from discord.ext import commands
from discord_slash import manage_components
from module import LaytheClient, AuthorEmbed, EmbedColor, Pager, Cursor, TrackEmbed


class Music(commands.Cog, name="음악"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot
        self.bot.loop.create_task(self.add_lavalink_event())

    def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()

    async def add_lavalink_event(self):
        await self.bot.wait_until_ready()
        self.bot.lavalink.add_event_hook(self.main_event)

    async def main_event(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild: discord.Guild = self.bot.get_guild(int(event.player.guild_id))
            channel: discord.TextChannel = event.player.fetch("channel")
            await channel.send(f"대기열이 비어있고 모든 노래를 재생했어요. 음성 채널에서 나갈께요.")
            await self.bot.connect_to_voice(guild)
            await self.bot.lavalink.player_manager.destroy(guild.id)
        if isinstance(event, lavalink.events.TrackStartEvent):
            embed = TrackEmbed(event.track,
                               self.bot.get_guild(int(event.player.guild_id)),
                               title="유튜브 음악 재생 - 재생 시작",
                               timestamp=self.bot.kst)
            channel = event.player.fetch("channel")
            await channel.send(embed=embed, delete_after=10)

    async def voice_check(self, ctx: commands.Context, *, check_connected: bool = False, check_playing: bool = False, check_paused: bool = False) -> tuple:
        voice: discord.VoiceState = ctx.author.voice

        if check_playing and check_paused:
            return 5, "코드에 문제가 있어요."

        if not voice or not voice.channel:
            return 1, "먼저 음성 채널에 들어와주세요."

        lava = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if check_connected and lava is None:
            return 2, "먼저 음악을 재생해주세요."

        if check_playing and lava.paused:
            return 3, "음악이 재생중이 아니에요. 먼저 음악을 재생해주세요."

        if check_paused and not lava.paused:
            return 4, "음악이 재생중이에요. 먼저 음악을 일시정지해주세요."

        return 0, None

    @commands.command(name="재생", description="음악을 재생해요.", usage="`{prefix}재생 [링크나 검색어:문자열]`", aliases=["play", "p", "ㅈ", "ㅔ"])
    async def play(self, ctx: commands.Context, *, url: str):
        code, text = await self.voice_check(ctx)
        if code:
            return await ctx.reply(text)
        loading = "<a:loading:868755640909201448>"
        await ctx.message.add_reaction(loading)
        url = url if url.startswith("https://") or url.startswith("http://") else f"ytsearch:{url}"
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.create(ctx.guild.id, region="ko")
        await self.bot.connect_to_voice(ctx.guild, ctx.author.voice) if not lava.is_connected else None
        resp = await lava.node.get_tracks(url)
        track = None
        if resp is None or len(resp["tracks"]) == 0:
            return await ctx.reply("영상을 찾지 못했어요. 링크가 정확한지 또는 검색어가 정확한지 확인해주세요.")

        if resp["loadType"] == "SEARCH_RESULT":
            tracks = resp["tracks"]
            base_embed = AuthorEmbed(ctx.author,
                                     title=f"유튜브 검색 결과 - 총 {len(tracks)}개",
                                     color=EmbedColor.DEFAULT)
            items = [f"[{x['info']['title']}]({x['info']['uri']})" for x in tracks]
            extra_button = manage_components.create_button(style=1, label="정보", custom_id="info")
            cursor = Cursor(self.bot, ctx.message, items, base_embed, extra_button=extra_button)
            async for comp_ctx, num in cursor.start_as_generator():
                track = tracks[num]
                embed = discord.Embed(title=f"영상 정보 - {track['info']['title']}",
                                      color=EmbedColor.NEUTRAL)
                embed.add_field(name="업로더", value=track["info"]["author"], inline=False)
                embed.add_field(name="링크", value=track["info"]["uri"], inline=False)
                embed.set_image(url=f"https://img.youtube.com/vi/{track['info']['identifier']}/hqdefault.jpg")
                comp_ctx._deferred_hidden = True
                comp_ctx.responded = True
                await comp_ctx.send(embed=embed, hidden=True)
            _msg, resp = cursor.result
            await _msg.delete()
            if resp is None:
                return await ctx.reply("재생을 취소했어요.")
            track = tracks[resp]
        elif resp["loadType"] == "PLAYLIST_LOADED":
            conf = await ctx.reply(f"재생목록이 감지되었어요. 재생목록의 모든 영상을 추가할까요?")
            y_or_n = await self.bot.confirm(ctx.author, conf)
            if not y_or_n:
                return await conf.edit(content=f"재생을 취소했어요.")
            track = resp["tracks"]
        track = track or resp["tracks"][0]
        if isinstance(track, list):
            [lava.add(requester=ctx.author.id, track=x) for x in track]
        elif track:
            lava.add(requester=ctx.author.id, track=track)
        await ctx.message.remove_reaction(loading, ctx.me)
        await ctx.message.add_reaction("✅")
        if not lava.is_playing:
            lava.store("channel", ctx.channel)
            return await lava.play()
        else:
            embed = TrackEmbed(lava.queue[-1],
                               ctx.guild,
                               title="유튜브 음악 재생 - 대기열에 추가됨",
                               timestamp=self.bot.kst)
            await ctx.reply(embed=embed, delete_after=10)

    @commands.command(name="스킵", description="재생중인 음악을 스킵해요.", aliases=["s", "skip", "ㄴ"])
    async def skip(self, ctx: commands.Context):
        code, text = await self.voice_check(ctx, check_connected=True, check_playing=True)
        if code:
            return await ctx.reply(text)
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await lava.skip()

    @commands.command(name="일시정지", description="음악 플레이어를 일시정지해요.", aliases=["pause", "ps", "ㅔㄴ"])
    async def pause(self, ctx: commands.Context):
        code, text = await self.voice_check(ctx, check_connected=True, check_playing=True)
        if code:
            return await ctx.reply(text)
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await lava.set_pause(True)
        await ctx.reply("✅ 음악 플레이어를 일시정지했어요.")

    @commands.command(name="재시작", description="음악 플레이어 일시정지를 해제해요", aliases=["resume", "r", "ㄱ"])
    async def resume(self, ctx: commands.Context):
        code, text = await self.voice_check(ctx, check_connected=True, check_paused=True)
        if code:
            return await ctx.reply(text)
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await lava.set_pause(False)
        await ctx.reply(f"✅ 일시정지를 해제했어요.")

    @commands.command(name="정지", description="음악 플레이어를 정지해요.", aliases=["stop", "ㄴ새ㅔ"])
    async def stop(self, ctx: commands.Context):
        code, text = await self.voice_check(ctx, check_connected=True)
        if code:
            return await ctx.reply(text)
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await lava.stop()
        await ctx.reply("✅ 음악 플레이어를 정지하고 모든 대기열을 삭제했어요. 음성 채널에서 나갈께요.")
        await self.bot.connect_to_voice(ctx.guild)
        await self.bot.lavalink.player_manager.destroy(ctx.guild.id)

    @commands.command(name="볼륨", description="음악 플레이어의 볼륨을 조절해요.", usage="`{prefix}볼륨 (볼륨값:숫자:현재 볼륨 보기)`", aliases=["volume", "vol", "v", "패ㅣㅕㅡㄷ", "ㅍ"])
    async def volume(self, ctx: commands.Context, vol: int = None):
        code, text = await self.voice_check(ctx, check_connected=True, check_playing=True)
        if code:
            return await ctx.reply(text)
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if vol is None:
            return await ctx.reply(f"ℹ 현재 볼륨은 `{lava.volume}`% 에요.")
        if not 0 < vol <= 1000:
            return await ctx.reply("❌ 볼륨 값은 1에서 1000 사이로만 가능해요.")
        await lava.set_volume(vol)
        await ctx.reply(f"✅ 볼륨을 `{vol}`%로 조정했어요.")


def setup(bot):
    bot.add_cog(Music(bot))
