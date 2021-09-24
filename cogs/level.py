import json
import math
import time
import random
import typing

import discord
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, LaytheSettingFlags, GuildEmbed, Pager
from module.utils import to_setting_flags


class Level(commands.Cog, name="레벨"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot
        self.bot.loop.create_task(self.init_cog())

    async def init_cog(self):
        await self.bot.wait_until_ready()
        await self.bot.cache.exec_sql("""DROP TABLE IF EXISTS level_cache""")
        await self.bot.cache.exec_sql("""CREATE TABLE IF NOT EXISTS level_cache ("guild_id" INTEGER NOT NULL, "user_id"INTEGER NOT NULL, "last_message_timestamp"INTEGER NOT NULL)""")

    @staticmethod
    def calc_exp_required(level):
        return 5 / 6 * level * (2 * level * level + 27 * level + 91)

    @commands.command(name="레벨제외", description="해당 채널에서 레벨링을 비활성화 해요.", usage="`{prefix}레벨제외 (채널:맨션 또는 ID:현재 채널)`")
    async def exclude_channel_from_leveling(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if "laythe:leveloff" in (channel.topic or ""):
            return await ctx.reply("❌ 이미 레벨링이 비활성화 돼있어요. 해당 채널에서 레벨링을 활성화하고 싶다면 해당 채널 주제에서 `laythe:leveloff` 문장을 삭제해주세요.")
        try:
            topic = channel.topic or ""
            topic += "\nlaythe:leveloff"
            await channel.edit(topic=topic)
            await ctx.reply("✅ 성공적으로 해당 채널에서 레벨링을 비활성화 했어요. 다시 활성화하고 싶다면 해당 채널 주제에서 `laythe:leveloff` 문장을 삭제해주세요.")
        except discord.DiscordException:
            await ctx.reply("❌ 레벨링 비활성화에 실패했어요. 해당 채널에서 저에서 채널 관리 권한이 없는 경우에 발생할 수 있어요. "
                            "수동으로 `laythe:leveloff` 문장을 해당 채널 주제에 넣어주세요. 다시 활성화하고 싶다면 해당 채널 주제에서 `laythe:leveloff` 문장을 삭제해주세요.")

    @commands.command(name="레벨", description="해당 유저의 레벨을 보여줘요.", usage="`{prefix}레벨 (유저:맨션 또는 ID:명령어를 사용한 유저)`")
    async def level(self, ctx: commands.Context, user: discord.Member = None):
        user = user or ctx.author
        level = await self.bot.db.fetch("""SELECT level, exp FROM levels WHERE guild_id=%s AND user_id=%s""", (ctx.guild.id, user.id))
        if not level:
            return await ctx.reply("ℹ 해당 유저의 레벨 기록이 존재하지 않아요.")
        level = level[0]
        lvl = level["level"]
        exp = level["exp"]
        embed = AuthorEmbed(user, title="레벨", color=EmbedColor.DEFAULT, timestamp=ctx.message.created_at)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="레벨", value=str(lvl))
        embed.add_field(name="EXP", value=str(exp))
        await ctx.reply(embed=embed)

    @commands.command(name="리더보드", description="해당 서버의 레벨 리더보드를 보여줘요.", aliases=["랭크"], usage="`{prefix}리더보드 (페이지 별 최대 개수:숫자:10)`")
    async def leaderboard(self, ctx: commands.Context, max_display: typing.Optional[int] = 10, test_mode: typing.Optional[bool] = False):
        flags = await self.bot.cache_manager.get_settings(ctx.guild.id, "flags")
        if not flags:
            return await ctx.reply("ℹ 해당 서버는 레벨 기능이 비활성화 돼있어요.")
        flags = to_setting_flags(flags[0]["flags"])
        if LaytheSettingFlags.USE_LEVEL not in flags:
            return await ctx.reply("ℹ 해당 서버는 레벨 기능이 비활성화 돼있어요.")

        level: list = await self.bot.db.fetch("""SELECT * FROM levels WHERE guild_id=%s ORDER BY exp DESC""", (ctx.guild.id,))
        if not level:
            return await ctx.reply("ℹ 해당 서버는 레벨 기록이 존재하지 않아요..")
        if test_mode and ctx.author.id == 288302173912170497:
            with open("dummy.json", "r", encoding="UTF-8") as f:
                level = [*reversed(sorted(json.load(f), key=lambda a: a['exp']))]
        base_embed = GuildEmbed(ctx.guild, title="레벨 리더보드", timestamp=ctx.message.created_at, color=EmbedColor.DEFAULT)
        had_author = False
        tgt = base_embed.copy()
        pages = []
        current_page = 1
        max_page = math.ceil(len(level)/max_display)
        author_level = [*filter(lambda n: n['user_id'] == ctx.author.id, level)]
        author_rank = 0
        if author_level:
            author_level = author_level[0]
            author_rank = level.index(author_level) + 1
        tgt.description = ""
        tgt.set_footer(text=f"페이지 {current_page}/{max_page}")
        for i, x in enumerate(level):
            if i > 0 and (i+1) % max_display == 1:
                if not had_author and author_level:
                    tgt.description += f"...\n\n#{author_rank}: <@{author_level['user_id']}>\n레벨 `{author_level['level']}` / EXP `{author_level['exp']}`"
                pages.append(tgt)
                tgt = base_embed.copy()
                current_page += 1
                tgt.set_footer(text=f"페이지 {current_page}/{max_page}")
                tgt.description = ""
            if ctx.author.id == x["user_id"]:
                had_author = True
            tgt.description += f"#{i+1}: <@{x['user_id']}>\n레벨 `{x['level']}` / EXP `{x['exp']}`\n\n"
        pages.append(tgt)
        pager = Pager(self.bot, ctx.channel, ctx.author, pages, is_embed=True, reply=ctx.message)
        await pager.start_flatten()

    @commands.command(name="레벨리셋", description="서버 전체 또는 선택한 유저의 레벨을 리셋해요.", usage="`{prefix}리더보드 (선택 유저:유저 ID 또는 맨션:서버 전체)`")
    @commands.has_permissions(manage_messages=True)
    async def reset_level(self, ctx: commands.Context, user: discord.User = None):
        msg = await ctx.send("정말로 레벨 리셋을 진행할까요?")
        conf = await self.bot.confirm(ctx.author, msg)
        if not conf:
            return await msg.edit(content="❌ 레벨 리셋을 취소했어요.")
        if user:
            await self.bot.db.execute("""DELETE FROM levels WHERE guild_id=%s AND user_id=%s""", (ctx.guild.id, user.id))
        else:
            await self.bot.db.execute("""DELETE FROM levels WHERE guild_id=%s""", (ctx.guild.id,))
        await msg.edit(content="✅ 성공적으로 레벨을 리셋했어요.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, discord.TextChannel) or "laythe:leveloff" in (message.channel.topic or ""):
            return

        flags = await self.bot.cache_manager.get_settings(message.guild.id, "flags")
        if not flags:
            return
        flags = to_setting_flags(flags[0]["flags"])
        if LaytheSettingFlags.USE_LEVEL not in flags:
            return

        cached = await self.bot.cache.res_sql("""SELECT last_message_timestamp FROM level_cache WHERE guild_id=? AND user_id=?""",  # noqa
                                              (message.guild.id, message.author.id))
        time_now = round(time.time())
        if not cached:
            await self.bot.cache.exec_sql("""INSERT INTO level_cache VALUES(?, ?, ?)""",  # noqa
                                          (message.guild.id, message.author.id, time_now))
        elif cached[0]["last_message_timestamp"]+60 > time_now:
            return
        await self.bot.cache.exec_sql("""UPDATE level_cache SET last_message_timestamp=? WHERE guild_id=? AND user_id=?""",  # noqa
                                      (time_now, message.guild.id, message.author.id))
        current = await self.bot.db.fetch("""SELECT exp, level FROM levels WHERE guild_id=%s AND user_id=%s""",
                                          (message.guild.id, message.author.id))
        if not current:
            await self.bot.db.execute("""INSERT INTO levels(guild_id, user_id) VALUES(%s, %s)""", (message.guild.id, message.author.id))
        exp = current[0]["exp"] if current else 0
        level = current[0]["level"] if current else 0
        level_up = False

        exp += random.randint(5, 25)
        required_exp = self.calc_exp_required(level+1)
        if required_exp < exp:
            level += 1
            level_up = True
            await message.channel.send(f"🎉 {message.author.mention}님의 레벨이 올라갔어요! (`{level-1}` -> `{level}`)")
        await self.bot.db.execute("""UPDATE levels SET exp=%s, level=%s WHERE guild_id=%s AND user_id=%s""",
                                  (exp, level, message.guild.id, message.author.id))
        if level_up:
            settings = (await self.bot.cache_manager.get_settings(message.guild.id, "reward_roles"))[0]
            if not settings["reward_roles"]:
                return
            reward_roles = json.loads(settings["reward_roles"])
            for k, v in sorted(reward_roles.items(), key=lambda n: n[0]):
                if level >= int(k):
                    tgt_role = message.guild.get_role(v)
                    if tgt_role:
                        await message.author.add_roles(tgt_role)
                else:
                    break


def setup(bot):
    bot.add_cog(Level(bot))
