import aiomysql
import aiosqlite


class LaytheDB:
    def __init__(self, host, port, login_id, login_pw, db_name):
        self.__connection = dict(host=host, port=port, user=login_id, password=login_pw, cursorclass=aiomysql.DictCursor, db=db_name)
        self.pool: aiomysql.Pool

    async def login(self):
        self.pool: aiomysql.Pool = await aiomysql.create_pool(**self.__connection, autocommit=True)

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def execute(self, sql: str, param: tuple = None):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, param)

    async def fetch(self, sql: str, param: tuple = None):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, param)
                return await cur.fetchall()


class SQLiteCache:
    def __init__(self, loop):
        # This is to load cache as fast as possible.
        self.db: aiosqlite.Connection = loop.run_until_complete(aiosqlite.connect(":memory:"))
        self.db.row_factory = aiosqlite.Row

    async def close(self):
        await self.db.close()

    async def exec_sql(self, line, param: iter = None):
        await self.db.execute(line, param)
        await self.db.commit()

    async def exec_many(self, line, params: iter = None):
        await self.db.executemany(line, params)
        await self.db.commit()

    async def res_sql(self, line, param: iter = None, return_raw=False) -> list:
        async with self.db.execute(line, param) as cur:
            rows = await cur.fetchall()
            if not return_raw:
                return [dict(x) for x in rows]
            return [x for x in rows]
