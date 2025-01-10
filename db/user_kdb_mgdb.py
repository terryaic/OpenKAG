import json
import os
import time
import pymongo
import sqlite3
from settings import MONGODB_HOST, MONGODB_PORT, DB_DEFAULT, SQLITE_DB_PATH,DBNAME
current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQLITE_DB_PATH)
# MongoDB 和 SQLite 的配置根据 DB_DEFAULT 进行选择
if DB_DEFAULT == "mongo":
    client = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
    db = client[DBNAME]

elif DB_DEFAULT == "sqlite":
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # 连接数据库并创建表
    try:
        db = sqlite3.connect(db_path, check_same_thread=False)
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kdb (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data JSON  -- 使用 JSON 类型存储整个 JSON 对象
            )
        """)
        db.commit()
    except sqlite3.OperationalError as e:
        print(f"Error initializing SQLite database: {e}")


def add_address_kdb(address, kdb_id):
    record = {
        "address":address,
        "kdb_id":kdb_id
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        return db.kdb.insert_one(record).inserted_id

    elif DB_DEFAULT == "sqlite":
        # SQLite 插入数据
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO kdb (data)
            VALUES (json_insert('{}', '$.address', ?, '$.kdb_id', ?))
        """, (address, kdb_id))
        db.commit()
        return cursor.lastrowid


def get_address(kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        return db.kdb.find_one({"kdb_id": kdb_id})

    elif DB_DEFAULT == "sqlite":
        # SQLite 查询数据
        cursor = db.cursor()
        cursor.execute("SELECT data FROM kdb WHERE json_extract (data, '$.kdb_id')= ?", (kdb_id,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None



def delete_kdb(kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        db.kdb.delete_one({"kdb_id": kdb_id})
        return True

    elif DB_DEFAULT == "sqlite":
        # SQLite 删除数据
        cursor = db.cursor()
        cursor.execute("DELETE FROM kdb WHERE json_extract(data, '$.kdb_id') = ?", (kdb_id,))
        db.commit()
        return True
