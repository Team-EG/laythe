import asyncio
import json
import math
import discord
from discord.ext import commands
from discord_slash.utils import manage_components
from module import LaytheClient, GuildEmbed, EmbedColor, Pager, LaytheSettingFlags
from module.utils import to_setting_flags, to_readable_bool


class Setting(commands.Cog, name="봇 설정"):
    def __init__(self, bot: LaytheClient):
        self.bot = bot

    @commands.group(name="설정", description="이 서버에서의 레이테 설정을 보거나 수정할 수 있어요.")
    @commands.has_permissions(administrator=True)
    async def laythe_setting(self, ctx: commands.Context):
        if ctx.invoked_subcommand:
            return
        settings = await self.bot.cache_manager.get_settings(ctx.guild.id)
        if not settings:
            return await ctx.reply("이런! 아직 레이테 설정을 사용할 수 없는 것 같아요... 최대 5분정도 기다린 뒤에 재시도해주세요.")
        settings = settings[0]
        flags = to_setting_flags(settings["flags"])
        reward_roles = json.loads(settings["reward_roles"] or "{}")
        reward_roles = {k: v for k, v in sorted(reward_roles.items(), key=lambda n: n[0])}
        embed = GuildEmbed(ctx.guild,
                           title="Laythe 설정 정보",
                           description=f"설정 변경은 `{ctx.prefix}설정 변경` 명령어로 할 수 있어요.",
                           color=EmbedColor.DEFAULT,
                           timestamp=ctx.message.created_at)
        embed.add_field(name="커스텀 프리픽스", value=settings["custom_prefix"] or "(없음)")
        embed.add_field(name="레벨 기능을 사용하나요?", value=to_readable_bool(LaytheSettingFlags.USE_LEVEL in flags))
        embed.add_field(name="뮤트 역할", value=f"<@&{settings['mute_role']}>" if settings['mute_role'] else "(없음)")
        embed.add_field(name="로그 채널", value=f"<#{settings['log_channel']}>" if settings['log_channel'] else "(없음)")
        embed.add_field(name="환영 채널", value=f"<#{settings['welcome_channel']}>" if settings['welcome_channel'] else "(없음)")
        embed.add_field(name="고정 채널", value=f"<#{settings['starboard_channel']}>" if settings['starboard_channel'] else "(없음)")
        embed.add_field(name="환영 메시지", value=settings["greet"] or "(없음)")
        embed.add_field(name="DM 환영 메시지", value=settings["greet_dm"] or "(없음)")
        embed.add_field(name="작별 인사 메시지", value=settings["bye"] or "(없음)")
        if not reward_roles:
            return await ctx.reply(embed=embed)
        pages = [embed]
        reward_embed = GuildEmbed(ctx.guild,
                                  title="레벨 리워드 역할",
                                  description=f"레벨 리워드 변경은 `{ctx.prefix}설정 변경` 명령어로 할 수 있어요.",
                                  color=EmbedColor.DEFAULT,
                                  timestamp=ctx.message.created_at)
        tgt = reward_embed.copy()
        current_page = 1
        max_page = math.ceil(len(reward_roles) / 5)
        tgt.set_footer(text=f"레벨 리워드 페이지 {current_page}/{max_page}")
        for i, x in enumerate(reward_roles):
            if i > 0 and (i+1) % 5 == 1:
                pages.append(tgt)
                tgt = reward_embed.copy()
                current_page += 1
                tgt.set_footer(text=f"레벨 리워드 페이지 {current_page}/{max_page}")
            role_id = reward_roles[x]
            tgt.add_field(name=f"레벨 {x}", value=f"<@&{role_id}>", inline=False)
        pages.append(tgt)
        pager = Pager(self.bot, ctx.channel, ctx.author, pages, is_embed=True, reply=ctx.message)
        await pager.start_flatten()

    @laythe_setting.command(name="변경")
    async def laythe_setting_update(self, ctx: commands.Context):
        settings = (await self.bot.cache_manager.get_settings(ctx.guild.id))[0]
        accepted = settings["accepted"]
        if not accepted:
            msg = await ctx.reply("레이테의 설정을 진행하기 전, 다음 이용 약관을 읽어주세요.\n"
                                  "레이테의 관리 기능을 사용하면, 해당 서버의 ID와 일부 기능에 사용되는 채널 ID, 그리고 경고 부여 시 경고를"
                                  "받은 유저의 ID를 수집합니다. 해당 내용에 동의하시지 않는 경우, 즉시 레이테 봇을 추방해주세요.\n"
                                  "계속 진행하신다면 해당 내용에 동의한 것으로 간주합니다.\n"
                                  "계속 진행할까요?")
            conf = await self.bot.confirm(ctx.author, msg)
            if not conf:
                return await msg.reply("이용 약관에 거부하셨어요. 만약 사용을 원하신다면 언제든지 이 명령어를 재실행해서 동의하실 수 있어요.\n"
                                       "그렇지 않다면, 바로 레이테 봇을 추방해주세요.")
            await msg.delete()
            await self.bot.db.execute("""UPDATE settings SET accepted=1 WHERE guild_id=%s""", (ctx.guild.id,))
            await self.bot.cache_manager.update_single_guild_setup(ctx.guild.id)
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
            label="레벨 리워드 역할", value="reward_roles"
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

                elif sel == "reward_roles":
                    if not wait_list.get("reward_roles"):
                        wait_list["reward_roles"] = settings["reward_roles"] or "{}"
                    waiting = json.loads(wait_list["reward_roles"])
                    msg = await init_msg.reply("30초 안에 설정하고 싶으신 레벨을 입력해주세요. 입력은 정수로만 해주세요.\n레벨 리워드 설정을 취소하고 싶으시다면 `취소` 라고 입력주세요.")
                    try:
                        _msg = await self.bot.wait_for("message",
                                                       check=lambda m: m.channel.id == ctx.channel.id and m.author.id == ctx.author.id,
                                                       timeout=30)
                        if _msg.content == "취소":
                            await msg.edit(content=f"ℹ 레벨 리워드 역할 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                            continue
                        level = int(_msg.content)
                        if level < 1:
                            raise ValueError
                    except ValueError:
                        await msg.edit(content=f"❌ 잘못된 입력이에요. 레벨 리워드 역할 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                        continue
                    except asyncio.TimeoutError:
                        await msg.edit(content=f"❌ 레벨 리워드 역할 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                        continue
                    level = str(level)
                    mention_role = f"<@&{waiting[level]}>" if level in waiting else ""
                    await msg.edit(content=f"30초 안에 레벨 {level}에서 지급할 역할을 선택해주세요.\n"
                                           "입력은 역할을 맨션하거나 역할 ID, 또는 역할 이름으로 할 수 있어요.\n"
                                           f"레벨 {level} 역할 설정을 취소하고 싶으시다면 `취소` 라고 입력주세요.\n"
                                           f"레벨 {level} 역할을 제거하고 싶으시면 `삭제` 라고 입력해주세요.\n"
                                           f"현재 설정: {mention_role or '`(설정 안됨)`'}",
                                   allowed_mentions=discord.AllowedMentions(roles=False))
                    try:
                        _msg = await self.bot.wait_for("message",
                                                       check=lambda m: m.channel.id == ctx.channel.id and m.author.id == ctx.author.id,
                                                       timeout=30)
                        if _msg.content == "취소":
                            await msg.edit(content=f"ℹ 레벨 {level} 리워드 역할 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                            continue
                        elif _msg.content == "삭제":
                            if level in waiting:
                                del waiting[level]
                            wait_list["reward_roles"] = json.dumps(waiting)
                            await msg.edit(content=f"✅ 레벨 {level} 리워드 역할이 성공적으로 삭제되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)
                            continue
                        try:
                            role = await commands.RoleConverter().convert(ctx, _msg.content)
                            waiting[level] = role.id
                            wait_list["reward_roles"] = json.dumps(waiting)
                            await msg.edit(content=f"✅ 레벨 {level} 리워드 역할 설정이 성공적으로 저장되었어요. 다시 위에서 다른 설정을 선택해주세요.",
                                           delete_after=5)
                        except commands.CommandError:
                            await msg.edit(content=f"❌ 존재하지 않는 역할이거나 잘못된 입력이에요. 레벨 {level} 리워드 역할 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.",
                                           delete_after=5)
                    except asyncio.TimeoutError:
                        await msg.edit(content=f"❌ 레벨 {level} 리워드 역할 설정이 취소되었어요. 다시 위에서 다른 설정을 선택해주세요.", delete_after=5)

                elif sel == "exit":
                    break
            except asyncio.TimeoutError:
                break
        await init_msg.delete()
        if not wait_list:
            return await ctx.reply("ℹ 변경된 설정이 없어요.")
        inject = ', '.join([f"{x}=%s" for x in wait_list.keys()])
        await self.bot.db.execute(f"""UPDATE settings SET {inject} WHERE guild_id=%s""", (*wait_list.values(), ctx.guild.id))
        try:
            kbot_voted, ubot_voted = await self.bot.botlist.get_voted(ctx.author.id)
        except:  # noqa
            kbot_voted = True
            ubot_voted = True
        extra_string = "\n기다리시는 동안 레이테에게 투표를 해주시는건 어떤가요? 투표는 다음 링크에서 할 수 있어요."
        if not kbot_voted:
            extra_string += "\nhttps://koreanbots.dev/bots/872349051620831292/vote (해당 링크에서 투표하신 경우 12시간마다 투표 여부가 초기화돼요.)"
        if not ubot_voted:
            extra_string += "\nhttps://uniquebots.kr/bots/info/872349051620831292"
        await ctx.reply(f"✅ 변경한 설정이 적용되었어요. 실제 적용까지는 최대 5분 정도 걸릴 수 있어요.{extra_string if not kbot_voted or not ubot_voted else ''}")


def setup(bot):
    bot.add_cog(Setting(bot))
