import math
import discord
import lavalink
from discord.ext import commands
from discord_slash import manage_components
from module import LaytheClient, AuthorEmbed, EmbedColor, Pager, Cursor, TrackEmbed, GuildEmbed
from module.utils import parse_second


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
            await channel.send(f"ℹ 대기열이 비어있고 모든 노래를 재생했어요. 음성 채널에서 나갈께요.")
            await self.bot.connect_to_voice(guild)
            await self.bot.lavalink.player_manager.destroy(guild.id)
        if isinstance(event, lavalink.events.TrackStartEvent):
            embed = TrackEmbed(event.track,
                               self.bot.get_guild(int(event.player.guild_id)),
                               title="유튜브 음악 재생 - 재생 시작",
                               timestamp=self.bot.kst)
            channel = event.player.fetch("channel")
            silent = event.player.fetch("silent")
            if not silent:
                await channel.send(embed=embed, delete_after=10)

    async def voice_check(self, ctx: commands.Context, *, check_connected: bool = False, check_playing: bool = False, check_paused: bool = False) -> tuple:
        voice: discord.VoiceState = ctx.author.voice

        if check_playing and check_paused:
            return 5, "❌ 코드에 문제가 있어요."

        if not voice or not voice.channel:
            return 1, "❌ 먼저 음성 채널에 들어와주세요."

        lava = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if check_connected and lava is None:
            return 2, "❌ 먼저 음악을 재생해주세요."

        if check_playing and lava.paused:
            return 3, "❌ 음악이 재생중이 아니에요. 먼저 음악을 재생해주세요."

        if check_paused and not lava.paused:
            return 4, "❌ 음악이 재생중이에요. 먼저 음악을 일시정지해주세요."

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
            return await ctx.reply("❌ 영상을 찾지 못했어요. 링크가 정확한지 또는 검색어가 정확한지 확인해주세요.")

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
                return await ctx.reply("❌ 재생을 취소했어요.")
            track = tracks[resp]
        elif resp["loadType"] == "PLAYLIST_LOADED":
            conf = await ctx.reply(f"ℹ 재생목록이 감지되었어요. 재생목록의 모든 영상을 추가할까요?")
            y_or_n = await self.bot.confirm(ctx.author, conf)
            if not y_or_n:
                return await conf.edit(content=f"❌ 재생을 취소했어요.")
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
            lava.store("silent", False)
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

    @commands.command(name="일시정지", description="음악 플레이어를 일시정지 하거나 일시정지를 해제해요.", aliases=["pause", "ps", "ㅔㄴ", "재시작", "resume", "r", "ㄱ"])
    async def pause(self, ctx: commands.Context):
        code, text = await self.voice_check(ctx, check_connected=True)
        if code:
            return await ctx.reply(text)
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await lava.set_pause(not lava.paused)
        await ctx.reply("✅ 음악 플레이어를 일시정지했어요." if lava.paused else "✅ 일시정지를 해제했어요.")

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

    @commands.command(name="셔플", description="대기 리스트에서 음악을 무작위로 재생해요.", aliases=["랜덤", "random", "shuffle", "sf", "ㄶ", "ㄴㅎ"])
    async def shuffle(self, ctx: commands.Context):
        code, text = await self.voice_check(ctx, check_connected=True)
        if code:
            return await ctx.reply(text)
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        lava.set_shuffle(not lava.shuffle)
        await ctx.send(f"✅ 랜덤 재생 기능이 {'켜졌어요!' if lava.shuffle else '꺼졌어요.'}")

    @commands.command(name='루프', description="재생중인 음악을 무한 반복하거나 무한 반복을 해제해요.", aliases=["무한반복", "loop", "repeat"])
    async def music_loop(self, ctx: commands.Context):
        code, text = await self.voice_check(ctx, check_connected=True)
        if code:
            return await ctx.reply(text)
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        lava.set_repeat(not lava.repeat)
        await ctx.send(f"✅ 반복 재생 기능이 {'켜졌어요!' if lava.repeat else '꺼졌어요.'}")

    @commands.command(name="사일렌트", description="음악 재생시 채널에 음악 재생 시작 메세지를 보낼지 결정해요.", aliases=["silent"])
    async def silent_mode(self, ctx: commands.Context):
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not lava:
            return await ctx.reply("❌ 먼저 아무 노래나 재생해주세요.")
        silent = lava.fetch("silent", False)
        lava.store("silent", not silent)
        await ctx.send(f"✅ 사일렌트 모드가 {'켜졌어요!' if not silent else '꺼졌어요.'}")

    @commands.command(name="대기열", description="현재 음악 대기열을 보여줘요.", aliases=["대기리스트", "ql", "pl", "np", "queuelist", "playlist", "비", "ㅔㅣ"])
    async def queue_list(self, ctx: commands.Context):
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not lava:
            return await ctx.reply("❌ 먼저 아무 노래나 재생해주세요.")
        front_embed = TrackEmbed(lava.current,
                                 ctx.guild,
                                 title="유튜브 음악 재생 - 현재 재생중",
                                 timestamp=self.bot.kst,
                                 show_requester=False)

        length = lava.current.duration / 1000
        now = lava._last_position / 1000
        percent = now / length
        pos = round(percent * 10)
        base = ["-" for _ in range(10)]
        base[pos if pos <= 9 else -1] = "o"
        vid = parse_second(round(length))
        cpos = parse_second(round(now))

        front_embed.add_field(name="요청자", value=f"<@{lava.current.requester}>", inline=False)
        front_embed.add_field(name="현재 볼륨", value=f"`{lava.volume}`%", inline=False)
        front_embed.add_field(name="대기중인 음악 개수", value=f"{len(lava.queue)}개")
        front_embed.set_footer(text=''.join(base) + f" | {cpos} / {vid}")
        if lava.paused:
            front_embed.add_field(name="플레이어 상태", value="⏸ 현재 일시정지 중이에요.", inline=False)
        elif lava.repeat:
            front_embed.add_field(name="플레이어 상태", value="🔂 반복 재생 기능이 켜져있어요.", inline=False)
        elif lava.shuffle:
            front_embed.add_field(name="플레이어 상태", value="🔀 랜덤 재생 기능이 켜져있어요.", inline=False)
        if len(lava.queue) == 0:
            return await ctx.send(embed=front_embed)
        pages = [front_embed]
        max_page = math.ceil(len(lava.queue)/5)
        base_embed = GuildEmbed(ctx.guild,
                                title="유튜브 음악 재생 - 음악 대기열",
                                description=f"총 {len(lava.queue)}개",
                                color=EmbedColor.DEFAULT,
                                timestamp=ctx.message.created_at)
        tgt = base_embed.copy()
        current_page = 1
        tgt.set_footer(text=f"대기열 페이지 {current_page}/{max_page}")
        for i, x in enumerate(lava.queue):
            if i > 0 and (i+1) % 5 == 1:
                pages.append(tgt)
                tgt = base_embed.copy()
                current_page += 1
                tgt.set_footer(text=f"대기열 페이지 {current_page}/{max_page}")
            tgt.add_field(name=f"#{i+1} - {x.title}", value=f"링크: {x.uri}\n요청자: <@{x.requester}>", inline=False)
        pages.append(tgt)

        last_embed = TrackEmbed(lava.queue[0],
                                ctx.guild,
                                title="유튜브 음악 재생 - 다음 음악",
                                color=EmbedColor.POSITIVE,
                                timestamp=ctx.message.created_at)

        pages.append(last_embed)

        pager = Pager(self.bot, ctx.channel, ctx.author, pages, is_embed=True, reply=ctx.message)
        await pager.start_flatten()


def setup(bot):
    bot.add_cog(Music(bot))
