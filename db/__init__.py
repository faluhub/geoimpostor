import json, os
from mysql import connector
from mysql.connector.abstracts import MySQLCursorAbstract

schemas = [
    "CREATE SCHEMA `geoimpostor` DEFAULT CHARACTER SET utf8mb4"
]

tables = [
    "CREATE TABLE `geoimpostor`.`users` (`user_id` BIGINT NOT NULL, `points` BIGINT NULL DEFAULT 0, PRIMARY KEY (`user_id`), UNIQUE INDEX `user_id_UNIQUE` (`user_id` ASC) VISIBLE)",
]

class Result:
    def __init__(self, cursor: MySQLCursorAbstract):
        self._cur = cursor
        self.rows = cursor.rowcount
    
    @property
    def value(self):
        fetch = self._cur.fetchone()
        if not fetch == None and not fetch[0] == None:
            if type(fetch[0]) == dict or type(fetch[0]) == list or (type(fetch[0]) == str and str(fetch[0])[0] in "{}[]"):
                return json.loads(fetch[0])
            else:
                return fetch[0]
        else:
            return None
    
    @property
    def value_all_raw(self):
        return self._cur.fetchall()

    @property
    def value_all(self):
        fetch = self._cur.fetchall()
        if not fetch is None:
            return [i[0] if len(i) == 1 else list(i) for i in fetch]
        return []

def connect():
    try:
        return connector.connect(
            host=os.environ["DB_HOST"],
            port=os.environ["DB_PORT"],
            user=os.environ["DB_USER"],
            passwd=os.environ["DB_PASSWORD"],
            use_unicode=True
        )
    except Exception as e:
        quit(f"Couldn't connect to DB: {e}")

def cursor(db):
    try:
        return db.cursor(buffered=True)
    except Exception as e:
        quit(f"Couldn't connect to DB's cursor: {e}")

def create():
    db = connect()
    cur = cursor(db)

    print("Creating schemas...")
    for i in schemas:
        schema = i.split("`")[1]
        try:
            cur.execute(i)
            db.commit()
            print(f"  Created schema '{schema}'")
        except Exception as e:
            print(f"  Error creating schema '{schema}': {e}")
    
    print("Creating tables...")
    for i in tables:
        table = i.split("`")[3]
        try:
            cur.execute(i)
            db.commit()
            print(f"  Created table '{table}'")
        except Exception as e:
            print(f"  Error creating table '{table}': {e}")
    
    cur.close()
    del cur

def select(q):
    db = connect()
    cur = cursor(db)
    cur.execute(q)
    return Result(cur)

def update(q):
    db = connect()
    cur = cursor(db)
    cur.execute(q)
    db.commit()
    cur.close()
    del cur
