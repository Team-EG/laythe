import aiosqlite


class SQLiteDB:
    def __init__(self, name, loop):
        self.db = loop.run_until_complete(aiosqlite.connect(f"db/{name}.db" if name != ":memory:" else ":memory:"))
        self.loop = loop
        self.db.row_factory = aiosqlite.Row

    def __del__(self):
        self.loop.create_task(self.db.close())

    async def execute(self, query: str, arg: iter = None):
        await self.db.execute(query, arg)
        await self.db.commit()

    async def fetch(self, query: str, arg: iter = None):
        async with self.db.execute(query, arg) as cursor:
            return [dict(x) for x in await cursor.fetchall()]
