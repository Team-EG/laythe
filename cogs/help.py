from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, Pager


class Help(commands.Cog, name="도움말"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.command(name="도움", description="도움말 명령어에요.", aliases=["help", "도움말", "commands", "명령어"])
    async def help(self, ctx: commands.Context):
        base_embed = AuthorEmbed(ctx.author,
                                 title="Laythe 명령어 리스트",
                                 description="필수로 채워야 하는 항목은 `[항목이름:타입]`이고, 선택적이면 `(항목이름:타입:기본값)`으로 표시돼요.",
                                 color=EmbedColor.DEFAULT,
                                 timestamp=ctx.message.created_at)
        fpage = base_embed.copy()
        pages = [fpage]
        for name, cog in self.bot.cogs.items():
            cmds = cog.get_commands()
            if name.startswith("PRIVATE_") or not cmds:
                continue
            fpage.add_field(name=name, value=', '.join([f"`{x.name}`" for x in cmds]), inline=False)
            cog_page = base_embed.copy()
            cog_page.title += f" - {name}"
            cpage = cog_page.copy()
            for n, x in enumerate(cmds):
                if n != 0 and n % 5 == 0:
                    pages.append(cpage)
                    cpage = cog_page.copy()
                cpage.add_field(name=x.name, value=(f"{x.description}\n"
                                                    f"사용법: {x.usage or f'`{ctx.prefix}{x.name}`'}"
                                                    + (f"\n별칭: `{'`, `'.join(x.aliases)}`" if x.aliases else "")).format(prefix=ctx.prefix), inline=False)
            pages.append(cpage)
        pager = Pager(self.bot, ctx.channel, ctx.author, pages, is_embed=True, reply=ctx.message)
        await pager.start_flatten()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and message.content.strip() in [f"<@!{self.bot.user.id}>", f"<@{self.bot.user.id}>"]:
            await message.reply("안녕하세요! 레이테 봇은 `레이테 [명령어]`, `laythe [명령어]`, `l![명령어]`로 사용할 수 있어요.\n"
                                "명령어 리스트는 `레이테 도움` 명령어를 참고해주세요.")


def setup(bot):
    bot.add_cog(Help(bot))
