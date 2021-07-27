import json
import typing
import asyncio
import logging
import datetime
import aiohttp
import discord
import lavalink
from contextlib import suppress
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.utils import manage_components
from .database import LaytheDB, SQLiteCache
from .cache import CacheManager
from extlib import BotList, SpellChecker


class LaytheClient(commands.AutoShardedBot):
    def __init__(self, logger: logging.Logger, **kwargs):
        intents = discord.Intents.all()
        intents.presences = False
        super().__init__(command_prefix=self.prefix,
                         help_command=None,
                         intents=intents,
                         allowed_mentions=discord.AllowedMentions(everyone=False))
        self.logger = logger
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.botlist = BotList(self, self.get_setting("kbot_token"), self.get_setting("ubot_token"), run_update=not self.is_debug)
        self.spell = SpellChecker(self.session)
        self.slash = SlashCommand(self)
        self.db = LaytheDB(self.get_setting("dbhost"),
                           self.get_setting("dbport"),
                           self.get_setting("dbid"),
                           self.get_setting("dbpw"),
                           self.get_setting("tgt_db"))
        self.cache = SQLiteCache(self.loop)
        self.cache_manager = CacheManager(self)
        self.db_ready = False
        self.lavalink: lavalink.Client
        self.loop.create_task(self.init_all_ext())

    @staticmethod
    def get_setting(key):
        with open("config.json", "r", encoding="UTF-8") as f:
            return json.load(f).get(key)

    @property
    def kst(self):
        return datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))

    @property
    def is_debug(self):
        return self.get_setting("debug")

    async def prefix(self, bot, message):
        prefixes = ["레이테 ", "laythe ", "Laythe ", "l!", "L!", "ㅣ!"]
        if not isinstance(message.channel, discord.TextChannel):
            return commands.when_mentioned_or(*prefixes)(bot, message)
        # bot_settings = await self.db.fetch("SELECT custom_prefix FROM settings WHERE guild_id=%s", (message.guild.id,))
        bot_settings = await self.cache_manager.get_settings(message.guild.id, "custom_prefix")
        if not bot_settings:
            # Try direct fetching first if not found on cache
            bot_settings = await self.db.fetch("SELECT custom_prefix FROM settings WHERE guild_id=%s",
                                               (message.guild.id,))
            if not bot_settings:
                await self.db.execute("INSERT INTO settings(guild_id) VALUES (%s)", (message.guild.id,))
                prefix = None
            else:
                prefix = bot_settings[0]["custom_prefix"]
            await self.cache_manager.update_single_guild_setup(message.guild.id)
        else:
            prefix = bot_settings[0]["custom_prefix"]
        if prefix:
            prefixes.append(prefix)
        return commands.when_mentioned_or(*prefixes)(bot, message)

    async def init_all_ext(self):
        await self.wait_until_ready()
        self.lavalink = lavalink.Client(self.user.id)
        self.lavalink.add_node(host=self.get_setting("lavahost"),
                               port=self.get_setting("lavaport"),
                               password=self.get_setting("lavapw"),
                               region="ko")
        self.add_listener(self.lavalink.voice_update_handler, "on_socket_response")
        await self.db.login()
        await self.cache_manager.update_cache()
        self.db_ready = True
        self.logger.info("DB and cache is all ready!")

    async def confirm(self, author: discord.User, message: discord.Message, timeout=30):
        yes_button = manage_components.create_button(3, "네", "⭕", f"yes{message.id}")
        no_button = manage_components.create_button(4, "아니요", "❌", f"no{message.id}")
        action_row = manage_components.create_actionrow(yes_button, no_button)
        await message.edit(components=[action_row])
        try:
            ctx = await manage_components.wait_for_component(
                self, message, action_row, check=lambda comp_ctx: int(comp_ctx.author_id) == int(author.id), timeout=timeout
            )
            await ctx.defer(edit_origin=True)
            return ctx.custom_id.startswith("yes")
        except asyncio.TimeoutError:
            return None
        finally:
            yes_button = manage_components.create_button(3, "네", "⭕", f"yes{message.id}", disabled=True)
            no_button = manage_components.create_button(4, "아니요", "❌", f"no{message.id}", disabled=True)
            action_row = manage_components.create_actionrow(yes_button, no_button)
            await message.edit(components=[action_row])

    async def connect_to_voice(self, guild: discord.Guild, voice: discord.VoiceState = None):
        ws = self.shards[guild.shard_id]._parent.ws
        await ws.voice_state(str(guild.id), voice.channel.id if voice else None)

    async def execute_guild_log(self, guild: discord.Guild, **kwargs):
        if not guild:
            return
        setting = await self.cache_manager.get_settings(guild.id, "log_channel")
        log_channel: int = setting[0]["log_channel"]
        if not log_channel:
            return False
        log_channel: discord.TextChannel = guild.get_channel(log_channel)
        return await log_channel.send(**kwargs)

    async def safe_clear_reactions(self, message: discord.Message):
        reactions = message.reactions
        try:
            await message.clear_reactions()
        except discord.Forbidden:
            [await x.remove(self.user) for x in reactions]

    @staticmethod
    async def safe_clear_reaction(reaction: discord.Reaction, user: typing.Union[discord.User, discord.Member]):
        with suppress(discord.Forbidden):
            await reaction.remove(user)

    def run(self):
        super().run(self.get_setting("dev_token" if self.is_debug else "token"))

    async def close(self):
        for x in self.lavalink.node_manager.nodes:
            await self.lavalink.node_manager.remove_node(x)
        await self.db.close()
        await self.cache.close()
        await self.session.close()
        await super().close()
