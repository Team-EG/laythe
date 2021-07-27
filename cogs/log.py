import discord
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, GuildEmbed, EmbedColor


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



def setup(bot):
    bot.add_cog(Log(bot))
