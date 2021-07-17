import aiomysql


class LaytheDB:
    def __init__(self, host, port, login_id, login_pw, db_name):
        self.__connection = dict(host=host, port=port, user=login_id, password=login_pw, cursorclass=aiomysql.DictCursor, db=db_name)
        self.db: aiomysql.Connection

    async def login(self):
        self.db = await aiomysql.connect(**self.__connection)

    def close(self):
        if self.db and not self.db.closed:
            self.db.close()
