import json
import os
import time
import pymongo
import sqlite3
from settings import MONGODB_HOST, MONGODB_PORT, DB_DEFAULT, SQL_DB_PATH_2USERS,DBNAME
current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQL_DB_PATH_2USERS)
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
        db = sqlite3.connect(db_path)
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


def get_user_role(user_id):
        # SQLite 查询数据
        db = sqlite3.connect(db_path)
        cursor = db.cursor()
        cursor.execute("SELECT role FROM users WHERE email = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None
