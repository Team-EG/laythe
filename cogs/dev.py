import os
import types
import datetime
import platform
import traceback
import psutil
import discord
import discord_slash
from discord.ext import commands
from module import LaytheClient, AuthorEmbed, EmbedColor, utils


class Dev(commands.Cog):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.group(name="dev")
    @commands.is_owner()
    async def dev(self, ctx: commands.Context):
        if ctx.invoked_subcommand:
            return

        kvote, uvote = await self.bot.botlist.get_vote_count()
        embed = AuthorEmbed(ctx.author,
                            title="Laythe 개발자 패널",
                            description=f"<:python:815496209682006036> Python `{platform.python_version()}` | "
                                        f"<:dpy2:815496751452651540> discord.py `{discord.__version__}` | "
                                        f"<:slash:815496477224468521> discord-py-slash-command `{discord_slash.__version__}`\n"
                                        f"플랫폼: `{platform.platform()}`\n"
                                        f"길드 `{len(self.bot.guilds)}`개 | 유저 `{len(self.bot.users)}`명\n"
                                        f"[KOREANBOTS](https://koreanbots.dev/bots/622710354836717580) `{kvote}` ❤ | "
                                        f"[UNIQUEBOTS](https://uniquebots.kr/bots/info/622710354836717580) `{uvote}` ❤",
                            timestamp=ctx.message.created_at,
                            color=EmbedColor.DEFAULT,
                            display_footer=True)
        privileged = ["members", "presences"]
        embed.add_field(name="활성화된 인텐트",
                        value=f"{', '.join([f'__`{x[0]}`__' if x[0] in privileged else f'`{x[0]}`' for x in self.bot.intents if x[1]])}",
                        inline=False)
        embed.add_field(name="샤드",
                        value=f"총 `{len(self.bot.shards)}`개 (이 길드 샤드 ID: `{ctx.guild.shard_id}`)"
                        if issubclass(type(self.bot), discord.AutoShardedClient) or self.bot.shard_count else
                        "⚠ 레이테가 현재 샤딩되지 않았습니다.",
                        inline=False)
        process = psutil.Process()
        memory = psutil.virtual_memory()
        uptime_sys = (datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())).total_seconds()
        uptime_bot = (datetime.datetime.now() - datetime.datetime.fromtimestamp(process.create_time())).total_seconds()
        embed.add_field(name="CPU 사용량",
                        value=f"총: `{psutil.cpu_percent()}`%\n"
                              f"쓰레드 당: `{'`% | `'.join([str(x) for x in psutil.cpu_percent(percpu=True)])}`%\n"
                              f"봇 프로세스: `{process.cpu_percent()}`%",
                        inline=False)
        embed.add_field(name="RAM 사용량",
                        value=f"총: `{memory.percent}`% ({utils.parse_bytesize(memory.used)}/{utils.parse_bytesize(memory.total)})\n"
                              f"봇 프로세스: (물리적: `{round(process.memory_percent('rss'), 2)}`% | "
                              f"가상: `{round(process.memory_percent('vms'), 2)}`%)",
                        inline=False)
        embed.add_field(name="업타임", value=f"서버: {utils.parse_second(round(uptime_sys))} | 봇: {utils.parse_second(round(uptime_bot))}", inline=False)
        embed.add_field(name="누적된 오류 로그 개수", value=f"`{len(os.listdir('traceback'))}`개", inline=False)
        await ctx.reply(embed=embed)

    @dev.command(name="eval")
    async def dev_eval(self, ctx: commands.Context, *, original_code: str):
        msg = await ctx.reply("잠시만 기다려주세요...")
        if original_code.startswith("```py") and original_code.endswith("```"):
            original_code = original_code.lstrip("```py\n")
            original_code = original_code.rstrip('```')
        if len(original_code.split('\n')) == 1 and not original_code.startswith("return"):
            original_code = f"return {original_code}"
        code = '\n'.join([f'    {x}' for x in original_code.split('\n')])
        code = f"async def execute_this(self, ctx):\n{code}"
        exec(compile(code, "<string>", "exec"))
        func = eval("execute_this")(self, ctx)
        embed = AuthorEmbed(ctx.author,
                            title="Laythe EVAL",
                            color=EmbedColor.DEFAULT,
                            timestamp=ctx.message.created_at,
                            display_footer=True)
        embed.add_field(name="입력", value=f"```py\n{original_code}\n```", inline=False)
        try:
            if isinstance(func, types.AsyncGeneratorType):
                await msg.delete()
                embed.add_field(name="결과", value="제너레이터 타입은 따로 출력됩니다.", inline=False)
                msg = await ctx.reply(embed=embed)
                count = 0
                async for x in func:
                    count += 1
                    yield_embed = discord.Embed(title=f"yield #{count}",
                                                description=f"""```py\n{f'"{x}"' if isinstance(x, str) else x}\n```""")
                    yield_embed.add_field(name="타입", value=f"```py\n{type(x)}\n```")
                    await msg.reply(embed=yield_embed)
            else:
                res = await func
                await msg.delete()
                embed.add_field(name="결과", value=f"""```py\n{f'"{res}"' if isinstance(res, str) else res}\n```""", inline=False)
                embed.add_field(name="타입", value=f"```py\n{type(res)}\n```", inline=False)
                await ctx.reply(embed=embed)
        except Exception as ex:
            await msg.delete()
            tb = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
            tb = ("..." + tb[-1997:]) if len(tb) > 2000 else tb
            embed.color = EmbedColor.NEGATIVE
            embed.add_field(name="Traceback", value=f"```py\n{tb}\n```", inline=False)
            await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Dev(bot))
