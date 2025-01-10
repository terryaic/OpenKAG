import json
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from databases import Database
from settings import MONGODB_HOST, MONGODB_PORT, DB_DEFAULT, SQLITE_DB_PATH,DBNAME
from db.spider_db import delete_spider_data

current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQLITE_DB_PATH)

# MongoDB 设置
if DB_DEFAULT == "mongo":
    client = AsyncIOMotorClient(MONGODB_HOST, MONGODB_PORT)
    db = client[DBNAME] # MongoDB 中的蜘蛛数据库

# SQLite 设置
elif DB_DEFAULT == "sqlite":
    db = Database(f"sqlite:///{db_path}?check_same_thread=False")
# 确保数据库表存在（SQLite）
CREATE_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS file_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data JSON  -- 使用 JSON 类型存储整个 JSON 对象
);
"""

# 异步插入数据
async def insert_file_info(kdb_id, is_scrapy, create_time, address):
    record = {
        "kdb_id": kdb_id,
        "is_scrapy": is_scrapy,
        "create_time": create_time,
        "address": address
    }

    if DB_DEFAULT == "mongo":
        await db.file_data.insert_one(record)
    elif DB_DEFAULT == "sqlite":
        await db.connect()
        # 确保表结构存在
        await db.execute("""
                    CREATE TABLE IF NOT EXISTS file_info (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data JSON
                    )
                """)

        # 将记录转为 JSON 格式字符串
        record_json = json.dumps(record)

        # 插入数据到 SQLite 的 JSON 字段
        query = """
                INSERT INTO file_info (data) VALUES (:data)
                """
        await db.execute(query, {"data": record_json})
        await db.disconnect()

# 异步查询数据
# async def get_file_info(address):
#     if DB_DEFAULT == "mongo":
#         return await db.spider_data.find_one({"address": address})
#     elif DB_DEFAULT == "sqlite":
#         await db.connect()
#         query = "SELECT data FROM file_info WHERE json_extract(data, '$.address') = :address"
#         result = await db.fetch_one(query, {"address": address})
#         await db.disconnect()
#         return json.loads(result["data"]) if result else None

# 异步删除数据
async def delete_file(address):
    print("shanchu")
    if DB_DEFAULT == "mongo":
        print(address)
        record = await db.file_data.find_one({"address": address})

        print("record in delete_file :",record)
        if record:
            # 如果记录存在，并且 is_scrapy 为 True，调用 delspider 函数
            if record.get("is_scrapy"):
                print('执行删除爬虫')
                await delete_spider_data(record["address"])  # 调用 delspider 函数
            # 删除 MongoDB 中的文档
            await db.file_data.delete_one({"address": address})

    elif DB_DEFAULT == "sqlite":
        await db.connect()
        query = "SELECT data FROM file_info WHERE json_extract(data, '$.address') = :address"
        result = await db.fetch_one(query, {"address": address})

        if result:
            data = json.loads(result["data"])  # 从 JSON 格式中提取字段
            if data.get("is_scrapy"):
                await delete_spider_data(data["address"])  # 调用 delspider 函数

        await db.execute("DELETE FROM file_info WHERE json_extract(data, '$.address') = :address", {"address": address})
        await db.disconnect()

    return True


async def update_create_time(kdb_id, address, new_create_time):
    """
    异步修改指定 kdb_id 和 address 的 create_time 字段
    :param kdb_id: 目标记录的 kdb_id
    :param address: 目标记录的文件地址
    :param new_create_time: 要更新的新的 create_time 值
    """
    if DB_DEFAULT == "mongo":
        # MongoDB 更新操作
        result = await db.file_data.update_one(
            {"kdb_id": kdb_id, "address": address},  # 匹配条件
            {"$set": {"create_time": new_create_time}}  # 设置新的 create_time
        )
        return result.modified_count  # 返回修改的文档数

    elif DB_DEFAULT == "sqlite":
        await db.connect()
        
        # 检查记录是否存在
        query_check = """
            SELECT id, data FROM file_info WHERE json_extract(data, '$.kdb_id') = :kdb_id
            AND json_extract(data, '$.address') = :address
        """
        result = await db.fetch_one(query_check, {"kdb_id": kdb_id, "address": address})
        
        if result is None:
            # 如果未找到记录
            await db.disconnect()
            return 0  # 无记录被修改
        
        # 提取现有记录并更新 `create_time`
        record = json.loads(result["data"])
        record["create_time"] = new_create_time
        updated_record_json = json.dumps(record)
        
        # 更新 SQLite 中的记录
        query_update = """
            UPDATE file_info SET data = :data WHERE id = :id
        """
        await db.execute(query_update, {"data": updated_record_json, "id": result["id"]})
        await db.disconnect()
        
        return 1  # 一条记录被修改
