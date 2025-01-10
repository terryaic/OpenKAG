import asyncio
import json
import os

from motor.motor_asyncio import AsyncIOMotorClient
from databases import Database
from settings import MONGODB_HOST, MONGODB_PORT, DB_DEFAULT, DBNAME, SQLITE_DB_PATH
current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQLITE_DB_PATH)
print(db_path)
db_url = f"sqlite:///{db_path}"
# 配置数据库连接
if DB_DEFAULT == "mongo":
    client = AsyncIOMotorClient(f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/")
    db = client[DBNAME]
elif DB_DEFAULT == "sqlite":
    database = Database(db_url)

# 定义表格结构（SQLite）
CREATE_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS history (
    session_id TEXT,
    date TEXT,
    context JSON  -- 使用 JSON 类型存储 context 字段
);
"""



# 异步插入数据
async def insert_session_data(data):
    if DB_DEFAULT == "mongo":
        collection = db['history']
        print("已插入对话data：", data)
        await collection.insert_one(data)
    elif DB_DEFAULT == "sqlite":
        # 确保数据库连接和表存在
        await database.connect()
        await database.execute(CREATE_TABLE_SQLITE)  # 确保表存在

        context_json = json.dumps(data['context'])
        # 直接将 context 字段作为 JSON 存储
        query = """
        INSERT INTO history (session_id, date, context) 
        VALUES (:session_id, :date, :context)
        """
        # 传入 session_id, date 和 context 数据
        await database.execute(query, {
            "session_id": data['session_id'],
            "date": data['date'],
            "context": context_json  # context 字段直接作为 JSON 数据存储
        })
        await database.disconnect()


async def delete_session_data(session_id):
    if DB_DEFAULT == "mongo":
        collection = db['history']
        data = {"session_id": session_id}
        print("尝试删除对话数据：", data)
        result = await collection.delete_one(data)
        if result.deleted_count > 0:
            print("MongoDB 删除成功")
            return True
        else:
            print("MongoDB 删除失败")
            return False
    elif DB_DEFAULT == "sqlite":
        try:
            # 确保数据库连接和表存在
            await database.connect()
            await database.execute(CREATE_TABLE_SQLITE)  # 确保表存在

            # 执行删除操作
            query = """
            DELETE FROM history 
            WHERE session_id = :session_id
            """
            rows_affected = await database.execute(query, {
                "session_id": session_id
            })
            await database.disconnect()

            if rows_affected > 0:
                print("SQLite 删除成功")
                return True
            else:
                print("SQLite 删除失败")
                return False
        except Exception as e:
            print("SQLite 删除时发生错误:", str(e))
            return False


# 异步获取数据
async def get_context_sessionid(session_id, in_reverse=True):
    allres = []

    if DB_DEFAULT == "mongo":
        collection = db['history']
        # 按照 _id 降序查询数据
        results = collection.find({"session_id": session_id}).sort("_id", -1 if in_reverse else 1)
        async for result in results:
            # 直接获取 context 字段
            context = result.get("context")
            allres.append(context)

    elif DB_DEFAULT == "sqlite":
        await database.connect()
        await database.execute(CREATE_TABLE_SQLITE)  # 确保表存在

        query = "SELECT context FROM history WHERE session_id = :session_id"
        rows = await database.fetch_all(query, {"session_id": session_id})

        for row in rows:
            # 直接获取 context 字段（SQLite 中存储为 JSON 格式）
            context = row['context']
            if isinstance(context, str):  # 如果 context 是字符串类型
                context = json.loads(context)
            # SQLite 返回的是 JSON 类型
            allres.append(context)

        # 反转返回结果，以便最新的记录在前
        if in_reverse:
            allres.reverse()
        print("allres:",allres)
        await database.disconnect()

    return allres

# async def show_all():
#     uri = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/"
#
#     async def display_all_data():
#         client = AsyncIOMotorClient(uri)
#         try:
#             db = client['history_sessionid']
#             collection = db['session_id_context']
#             all_data = collection.find()
#
#             async for document in all_data:
#                 print(document)
#
#         except Exception as e:
#             print("Error occurred:", e)
#         finally:
#             client.close()
# ##cdced1
#     await display_all_data()
# from pymongo import MongoClient
#
# def display_session_data(session_id):
#     # 连接到 MongoDB
#     client = MongoClient(f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/")
#     db = client['history_sessionid']  # 替换为你的数据库名
#     collection = db['session_id_context']  # 替换为你的集合名
#
#     # 查询特定 session_id 的所有内容
#     results = collection.find({'session_id': session_id})
#
#     # 打印结果
#     for document in results:
#         print(document)
#
#     # 关闭连接
#     client.close()

if __name__ == "__main__":
    import asyncio

    # 替换为要查找的 session_id
    session_id_to_find = "e1f9b071dfef4e6e89772c3fbd9f1020"

    async def main():
        # 调用 get_context_sessionid 查询数据
        results = await get_context_sessionid(session_id_to_find)

        # 打印结果
        if results:
            print(f"找到的上下文数据（session_id: {session_id_to_find}）:")
            for context in results:
                print(context)
        else:
            print(f"未找到 session_id 为 {session_id_to_find} 的数据。")

    # 运行异步主函数
    asyncio.run(main())