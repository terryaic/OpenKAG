import json
import os
import pymongo
import sqlite3

from motor.motor_asyncio import AsyncIOMotorClient
from settings import MONGODB_HOST, MONGODB_PORT, DB_DEFAULT, DBNAME, SQLITE_DB_PATH
from databases import Database
current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQLITE_DB_PATH)


db_url = f"sqlite:///{db_path}"
# 配置数据库连接
if DB_DEFAULT == "mongo":
    client = AsyncIOMotorClient(f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/")
    db = client[DBNAME]
elif DB_DEFAULT == "sqlite":
    database = Database(db_url)

# 定义表格结构（SQLite）
CREATE_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS spider_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data JSON  -- 使用 JSON 类型存储整个 JSON 对象
    )
"""


# 插入数据
import json


async def insert_spider_data(url, create_time, name,address):
    # 构造记录对象
    record = {
        "url": url,
        "create_time": create_time,
        "name": name,
        "address":address
    }

    if DB_DEFAULT == "mongo":
        collection = db['spider_data']
        print("插入数据到 MongoDB:", record)
        await collection.insert_one(record)

    elif DB_DEFAULT == "sqlite":
        # 确保数据库连接和表存在
        await database.connect()
        # 确保表结构存在
        await database.execute("""
            CREATE TABLE IF NOT EXISTS spider_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data JSON
            )
        """)

        # 将记录转为 JSON 格式字符串
        record_json = json.dumps(record)

        # 插入数据到 SQLite 的 JSON 字段
        query = """
        INSERT INTO spider_data (data) VALUES (:data)
        """
        await database.execute(query, {"data": record_json})
        await database.disconnect()

    return True


# 查询数据
# def get_spider_data(url):
#     if DB_DEFAULT == "mongo":
#         return db.spider_data.find_one({"url": url})
#     elif DB_DEFAULT == "sqlite":
#         cursor = db.cursor()
#         cursor.execute("SELECT data FROM spider_data WHERE json_extract(data, '$.url') = ?", (url,))
#         row = cursor.fetchone()
#         return json.loads(row[0]) if row else None


# 删除数据
async def delete_spider_data(address):
    print("address in delete_spider_data",delete_spider_data)
    if DB_DEFAULT == "mongo":
        collection = db['spider_data']
        await collection.delete_one({"address": address})
    elif DB_DEFAULT == "sqlite":
        # 确保数据库连接
        await database.connect()

        # 定义删除语句，并使用 json_extract 从 JSON 数据中获取 address 字段
        query = """
        DELETE FROM spider_data WHERE json_extract(data, '$.address') = :address
        """

        # 执行异步删除操作
        await database.execute(query, {"address": address})

        # 断开数据库连接
        await database.disconnect()

    return True
