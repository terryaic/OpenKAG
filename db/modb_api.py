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


import json

async def insert_session_file_upload(data, session_id):
    # 准备 context 数据
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    context = {
        "text": [{"filename": file['filename'], "filetype": file['filetype'], "filesize": file['filesize']} for file in data],  # 根据传入的文件列表构建
        "text_type": "file",
        "language": None,
        "role": "user"
    }
    #第一个文件的时间，如果有，其实就是没有使用现在时间，可选择新加参数data
    date = next((file.get("date") for file in data if "date" in file), current_date)
    # 插入数据到 MongoDB
    if DB_DEFAULT == "mongo":
        collection = db['history']
        # 构建要插入的文档,如果需要kdbid，在index.py的/conversation修改
        document = {
            "session_id": session_id,  # 使用传入的 session_id
            "date": date,
            "kdb_id": None,  # kdb_id 可能为 None
            "context": context
        }
        print("已插入file记录：", document)
        await collection.insert_one(document)

    # 插入数据到 SQLite
    if DB_DEFAULT == "sqlite":
        # 确保数据库连接和表存在
        await database.connect()
        await database.execute(CREATE_TABLE_SQLITE)  # 确保表存在

        # 将 context 字典转为 JSON 字符串
        context_json = json.dumps(context)

        # 获取第一个文件的 kdb_id，若没有则为 None，现在sql没有kdbid列
        #kdb_id = next((file.get("kdb_id") for file in data if "kdb_id" in file), None)

        # 插入数据到 SQLite
        query = """
            INSERT INTO history (session_id, date, context) 
            VALUES (:session_id, :date, :context)
        """
        await database.execute(query, {
            "session_id": session_id,  # 使用传入的 session_id
            "date": date,  # 使用文件列表中获取的 date
            "context": context_json  # 将 context 存储为 JSON 字符串
        })

        # 断开数据库连接
        await database.disconnect()


#给onmessage显示用的
async def get_file_record(session_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询操作
        collection = db['history']
        # 查询符合条件的记录，按日期升序排序
        result = await collection.find_one(
            {"session_id": session_id, "context.text_type": "file"},  # 查询条件
            sort=[("date", 1)]  # 按日期升序排序
        )
        # 如果找到结果，返回 context['text'] 列表
        if result and "context" in result and "text" in result["context"]:
            return result["context"]["text"]
        return None

    elif DB_DEFAULT == "sqlite":
        # SQLite 查询操作
        await database.connect()

        query = """
        SELECT context 
        FROM history 
        WHERE session_id = :session_id 
          AND json_extract(context, '$.text_type') = 'file' 
        ORDER BY date ASC
        LIMIT 1;
        """
        params = {"session_id": session_id}
        result = await database.fetch_one(query, params)
        await database.disconnect()

        # 如果找到结果，解析 context 并返回 context['text']
        if result:
            context = json.loads(result["context"])
            if "text" in context:
                return context["text"]
        return None
    

async def get_all_file_record(session_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询操作
        collection = db['history']
        # 查询符合条件的记录，按日期升序排序
        result = await collection.find(
            {"session_id": session_id, "context.text_type": "file"},  # 查询条件
            sort=[("date", 1)]  # 按日期升序排序
        ).to_list(length=None)
        # 如果找到结果，返回 context['text'] 列表
        file = []
        if result:
            for info in result:
                file.append(info["context"]["text"])
        return file

    elif DB_DEFAULT == "sqlite":
        # SQLite 查询操作
        await database.connect()

        query = """
        SELECT context 
        FROM history 
        WHERE session_id = :session_id 
        AND json_extract(context, '$.text_type') = 'file' 
        ORDER BY date ASC;
        """
        params = {"session_id": session_id}
        result = await database.fetch_all(query, params)
        await database.disconnect()

        # 如果找到结果，解析 context 并返回 context['text']
        if result:
            print("获取的结果是",result)
            all_texts = []  # 用于保存所有找到的 text
            for record in result:
                context = json.loads(record["context"])  # 解析每条记录的 context
                if "text" in context:
                    all_texts.append(context["text"])  # 将 text 添加到列表中
            return all_texts if all_texts else []  # 如果有找到 text，则返回，否则返回 None
        return []  # 没有找到任何结果时返回 None


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