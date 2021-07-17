import time
import random
import discord
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor


class Level(commands.Cog, name="레벨"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot
        self.bot.loop.create_task(self.init_cog())

    async def init_cog(self):
        await self.bot.wait_until_ready()
        await self.bot.cache.exec_sql("""CREATE TABLE IF NOT EXISTS level_cache ("guild_id" INTEGER NOT NULL, "user_id"INTEGER NOT NULL, "last_message_timestamp"INTEGER NOT NULL)""")

    @staticmethod
    def calc_exp_required(level):
        return 5 / 6 * level * (2 * level * level + 27 * level + 91)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, discord.TextChannel) or "laythe:leveloff" in (message.channel.topic or ""):
            return

        cached = await self.bot.cache.res_sql("""SELECT last_message_timestamp FROM level_cache WHERE guild_id=? AND user_id=?""",
                                              (message.guild.id, message.author.id))
        time_now = round(time.time())
        if not cached:
            await self.bot.cache.exec_sql("""INSERT INTO level_cache VALUES(?, ?, ?)""",
                                          (message.guild.id, message.author.id, time_now))
            return
        elif cached[0]["last_message_timestamp"]+60 > time_now:
            return
        await self.bot.cache.exec_sql("""UPDATE level_cache SET last_message_timestamp=? WHERE guild_id=? AND user_id=?""",
                                      (time_now, message.guild.id, message.author.id))
        current = await self.bot.db.fetch("""SELECT exp, level FROM levels WHERE guild_id=%s AND user_id=%s""",
                                          (message.guild.id, message.author.id))
        if not current:
            await self.bot.db.execute("""INSERT INTO levels(guild_id, user_id) VALUES(%s, %s)""", (message.guild.id, message.author.id))
        exp = current[0]["exp"] if current else 0
        level = current[0]["level"] if current else 0

        exp += random.randint(5, 25)
        required_exp = self.calc_exp_required(level+1)
        if required_exp < exp:
            level += 1
            await message.channel.send(f"🎉 {message.author.mention}님의 레벨이 올라갔습니다! (`{level-1}` -> `{level}`)")
        await self.bot.db.execute("""UPDATE levels SET exp=%s, level=%s WHERE guild_id=%s AND user_id=%s""",
                                  (exp, level, message.guild.id, message.author.id))


def setup(bot):
    bot.add_cog(Level(bot))
