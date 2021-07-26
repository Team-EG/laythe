class CacheManager:
    def __init__(self, bot):
        self.bot = bot

    async def update_cache(self):
        await self.bot.wait_until_ready()
        await self.bot.cache.exec_sql("""CREATE TABLE IF NOT EXISTS settings_cache 
        ("guild_id" INTEGER NOT NULL PRIMARY KEY,
        "custom_prefix" TEXT,
        "flags" INTEGER NOT NULL,
        "mute_role" INTEGER DEFAULT NULL,
        "log_channel" INTEGER DEFAULT NULL,
        "welcome_channel" INTEGER DEFAULT NULL,
        "starboard_channel" INTEGER DEFAULT NULL,
        "greet" TEXT DEFAULT NULL,
        "greet_dm" TEXT DEFAULT NULL,
        "bye" TEXT DEFAULT NULL,
        "reward_roles" TEXT DEFAULT NULL,
        "warn_actions" TEXT DEFAULT NULL)""")
        guild_settings = await self.bot.db.fetch("""SELECT * FROM settings""")
        await self.bot.cache.exec_many("""INSERT OR REPLACE INTO settings_cache VALUES(?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?)""",
                                       [tuple(x.values()) for x in guild_settings])

    async def get_settings(self, guild_id: int, *tgt: str):
        if not tgt:
            tgt = "*"
        else:
            tgt = ', '.join(tgt)
        return await self.bot.cache.res_sql(f"""SELECT {tgt} FROM settings_cache WHERE guild_id=?""", (guild_id,))  # noqa

    async def update_single_guild_setup(self, guild_id):
        setting = await self.bot.db.fetch("""SELECT * FROM settings WHERE guild_id=%s""", (guild_id,))
        await self.bot.cache.exec_sql("""INSERT OR REPLACE INTO settings_cache VALUES(?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?)""", tuple(setting[0].values()))
