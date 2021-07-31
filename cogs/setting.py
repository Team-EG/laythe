import asyncio

import discord
from discord.ext import commands
from discord_slash.utils import manage_components
from module import LaytheClient, GuildEmbed, EmbedColor, Pager, LaytheSettingFlags
from module.utils import to_setting_flags, to_readable_bool


class Setting(commands.Cog, name="봇 설정"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.group(name="설정", description="이 서버에서의 레이테 설정을 보거나 수정할 수 있어요.", usage="`{prefix}설정 도움` 명령어를 참고해주세요.")
    @commands.has_permissions(administrator=True)
    async def laythe_setting(self, ctx: commands.Context):
        if ctx.invoked_subcommand:
            return
        settings = await self.bot.cache_manager.get_settings(ctx.guild.id)
        if not settings:
            return await ctx.reply("이런! 아직 레이테 설정을 사용할 수 없는 것 같아요... 최대 5분정도 기다린 뒤에 재시도해주세요.")
        settings = settings[0]
        flags = to_setting_flags(settings["flags"])
        embed = GuildEmbed(ctx.guild, title="Laythe 설정 정보", color=EmbedColor.DEFAULT, timestamp=ctx.message.created_at)
        embed.add_field(name="커스텀 프리픽스", value=settings["custom_prefix"] or "(없음)")
        embed.add_field(name="레벨 기능을 사용하나요?", value=to_readable_bool(LaytheSettingFlags.USE_LEVEL in flags))
        embed.add_field(name="뮤트 역할", value=f"<@&{settings['mute_role']}>" if settings['mute_role'] else "(없음)")
        embed.add_field(name="로그 채널", value=f"<#{settings['log_channel']}>" if settings['log_channel'] else "(없음)")
        embed.add_field(name="환영 채널", value=f"<#{settings['welcome_channel']}>" if settings['welcome_channel'] else "(없음)")
        embed.add_field(name="고정 채널", value=f"<#{settings['starboard_channel']}>" if settings['starboard_channel'] else "(없음)")
        embed.add_field(name="환영 메시지", value=settings["greet"] or "(없음)")
        embed.add_field(name="DM 환영 메시지", value=settings["greet_dm"] or "(없음)")
        embed.add_field(name="작별 인사 메시지", value=settings["bye"] or "(없음)")
        await ctx.reply(embed=embed)

    @laythe_setting.command(name="도움")
    async def laythe_setting_help(self, ctx: commands.Context):
        pass

    @laythe_setting.command(name="변경")
    async def laythe_setting_update(self, ctx: commands.Context):
        settings = (await self.bot.cache_manager.get_settings(ctx.guild.id))[0]
        flags = to_setting_flags(settings["flags"])
        items = [manage_components.create_select_option(
            label="커스텀 프리픽스", value="custom_prefix"
        ), manage_components.create_select_option(
            label="레벨 기능 토글", value="level_toggle"
        ), manage_components.create_select_option(
            label="뮤트 역할", value="mute_role"
        ), manage_components.create_select_option(
            label="로그 채널", value="log_channel"
        ), manage_components.create_select_option(
            label="환영 채널", value="welcome_channel"
        ), manage_components.create_select_option(
            label="고정 채널", value="starboard_channel"
        ), manage_components.create_select_option(
            label="환영 메시지", value="greet"
        ), manage_components.create_select_option(
            label="DM 환영 메시지", value="greet_dm"
        ), manage_components.create_select_option(
            label="작별 인사 메시지", value="bye"
        ), manage_components.create_select_option(
            label="종료", value="exit"
        )]
        select = manage_components.create_select(items, custom_id=f"select{ctx.message.id}")
        row = manage_components.create_actionrow(select)
        wait_list = {}
        init_msg = await ctx.reply("다음 중 바꾸고 싶은 설정을 선택해주세요.", components=[row])
        while True:
            try:
                comp_ctx = await manage_components.wait_for_component(self.bot,
                                                                      [init_msg],
                                                                      row,
                                                                      timeout=60,
                                                                      check=lambda cc: int(cc.author_id) == int(
                                                                          ctx.author.id))
                await comp_ctx.defer(edit_origin=True)
                comp_ctx.responded = True
                sel = comp_ctx.selected_options[0]

                if sel in ["custom_prefix", "greet", "greet_dm", "bye"]:
                    names = {
                        "custom_prefix": "커스텀 프리픽스",
                        "greet": "환영 메시지",
                        "greet_dm": "DM 환영 메시지",
                        "bye": "작별 인사 메시지"
                    }
                    name = names.get(sel, sel)
                    extra_desc = "환영 메시지에 `{mention}`을 널으면 그 부분에 유저 맨션이 들어가고, DM 환영/작별 인사 메시지에 `{name}`을 넣으면 유저의 이름이 들어가게 할 수 있어요.\n"
                    msg = await init_msg.reply(f"30초 안에 설정하고 싶으신 {name}를 입력해주세요.\n{extra_desc if sel != 'custom_prefix' else ''}"
                                               f"{name} 설정을 취소하고 싶으시다면 `취소` 라고 입력주세요.\n"
                                               f"기존 {name}를 제거하고 싶으시면 `삭제` 라고 입력해주세요.\n"
                                               f"현재 설정: `{settings[sel] or '(설정 안됨)'}`")
                    try:
                        _msg = await self.bot.wait_for("message",
                                                       check=lambda m: m.channel.id == ctx.channel.id and m.author.id == ctx.author.id,
                                                       timeout=30)
                        if _msg.content == "취소":
                            await msg.edit(content=f"ℹ {name} 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                            continue
                        wait_list[sel] = _msg.content if _msg.content != "삭제" else None
                        await msg.edit(content=f"✅ {name} 설정이 성공적으로 저장되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                    except asyncio.TimeoutError:
                        await msg.edit(content=f"❌ {name} 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)

                elif sel == "level_toggle":
                    is_enabled = LaytheSettingFlags.USE_LEVEL in flags
                    msg = await init_msg.reply(f"레벨 기능을 {'끌까요' if is_enabled else '켤까요'}?")
                    resp = await self.bot.confirm(ctx.author, msg)
                    if resp:
                        await msg.edit(content=f"✅ 레벨 기능을 {'껐어요' if is_enabled else '켰어요'}. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                        flags.use_level = not is_enabled
                        wait_list["flags"] = int(flags)
                    else:
                        await msg.edit(content="❌ 레벨 기능 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)

                elif sel in ["log_channel", "welcome_channel", "starboard_channel"]:
                    names = {
                        "log_channel": "로그",
                        "welcome_channel": "환영",
                        "starboard_channel": "고정"
                    }
                    name = names.get(sel, sel)
                    mention_ch = f"<#{settings[sel]}>"
                    msg = await init_msg.reply(f"30초 안에 설정하고 싶으신 {name} 채널을 입력해주세요.\n"
                                               "입력은 채널을 맨션하거나 채널 ID, 또는 채널 이름으로 할 수 있어요.\n"
                                               f"{name} 채널 설정을 취소하고 싶으시다면 `취소` 라고 입력주세요.\n"
                                               f"{name} 채널을 제거하고 싶으시면 `삭제` 라고 입력해주세요.\n"
                                               f"현재 설정: {mention_ch if settings[sel] else '`(설정 안됨)`'}")
                    try:
                        _msg = await self.bot.wait_for("message",
                                                       check=lambda m: m.channel.id == ctx.channel.id and m.author.id == ctx.author.id,
                                                       timeout=30)
                        if _msg.content == "취소":
                            await msg.edit(content=f"ℹ {name} 채널 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                            continue
                        elif _msg.content == "삭제":
                            wait_list[sel] = None
                            await msg.edit(content=f"✅ {name} 채널이 성공적으로 삭제되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                            continue
                        try:
                            role = await commands.TextChannelConverter().convert(ctx, _msg.content)
                            wait_list[sel] = role.id
                            await msg.edit(content=f"✅ {name} 채널 설정이 성공적으로 저장되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                        except commands.CommandError:
                            await msg.edit(content=f"❌ 존재하지 않는 채널이거나 잘못된 입력이에요. {name} 채널 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                    except asyncio.TimeoutError:
                        await msg.edit(content=f"❌ {name} 채널 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)

                elif sel in ["mute_role"]:
                    names = {
                        "mute_role": "뮤트"
                    }
                    name = names.get(sel, sel)
                    mention_role = f"<@&{settings[sel]}>"
                    msg = await init_msg.reply(f"30초 안에 설정하고 싶으신 {name} 역할을 입력해주세요.\n"
                                               "입력은 역할을 맨션하거나 역할 ID, 또는 역할 이름으로 할 수 있어요.\n"
                                               f"{name} 역할 설정을 취소하고 싶으시다면 `취소` 라고 입력주세요.\n"
                                               f"{name} 역할을 제거하고 싶으시면 `삭제` 라고 입력해주세요.\n"
                                               f"현재 설정: {mention_role if settings[sel] else '`(설정 안됨)`'}",
                                               allowed_mentions=discord.AllowedMentions(roles=False))
                    try:
                        _msg = await self.bot.wait_for("message",
                                                       check=lambda m: m.channel.id == ctx.channel.id and m.author.id == ctx.author.id,
                                                       timeout=30)
                        if _msg.content == "취소":
                            await msg.edit(content=f"ℹ {name} 역할 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                            continue
                        elif _msg.content == "삭제":
                            wait_list[sel] = None
                            await msg.edit(content=f"✅ {name} 역할이 성공적으로 삭제되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                            continue
                        try:
                            role = await commands.RoleConverter().convert(ctx, _msg.content)
                            wait_list[sel] = role.id
                            await msg.edit(content=f"✅ {name} 역할 설정이 성공적으로 저장되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                        except commands.CommandError:
                            await msg.edit(content=f"❌ 존재하지 않는 역할이거나 잘못된 입력이에요. {name} 역할 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                    except asyncio.TimeoutError:
                        await msg.edit(content=f"❌ {name} 역할 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)

                elif sel == "exit":
                    break
            except asyncio.TimeoutError:
                break
        await init_msg.delete()
        if not wait_list:
            return await ctx.reply("ℹ 변경된 설정이 없어요.")
        inject = ', '.join([f"{x}=%s" for x in wait_list.keys()])
        await self.bot.db.execute(f"""UPDATE settings SET {inject} WHERE guild_id=%s""", (*wait_list.values(), ctx.guild.id))
        await ctx.reply("✅ 변경한 설정이 적용되었어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.")


def setup(bot):
    bot.add_cog(Setting(bot))
