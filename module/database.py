import aiomysql


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
