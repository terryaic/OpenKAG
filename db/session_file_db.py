import json
import os
import time
import pymongo
import sqlite3
from settings import MONGODB_HOST, MONGODB_PORT, DB_DEFAULT, SQLITE_DB_PATH,DBNAME
current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQLITE_DB_PATH)
# MongoDB 设置
if DB_DEFAULT == "mongo":
    client = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
    db = client[DBNAME]

# SQLite 设置
elif DB_DEFAULT == "sqlite":
    from .init_db import execute_sql
    sql_query ="""
            CREATE TABLE IF NOT EXISTS session_file (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            doc_id TEXT,
            session_id TEXT,
            original_filename TEXT,
            filename_with_timestamp TEXT,
            address TEXT,
            respath TEXT
        );
        """
    # 调用 execute_sql 函数执行 SQL 语句
    execute_sql(sql_query, None)


def addfile(file_id,session_id,original_filename, filename_with_timestamp, address,respath):
    record = {
        "file_id":file_id,
        "original_filename": original_filename,
        "filename_with_timestamp": filename_with_timestamp,
        "address": address,
        "respath": respath,
        "session_id":session_id
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.session_file.update_one(
            record,  # 匹配条件
            {"$set": record},  # 更新操作
            upsert=True  # 如果没有匹配的文档则插入新的
        )
        print("插入完成")
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                INSERT INTO session_file (file_id,session_id,original_filename, filename_with_timestamp, address, respath) VALUES (?, ?, ?, ?, ?, ?)
            """

        params = (file_id,session_id,original_filename, filename_with_timestamp, address, respath)
        result = execute_sql(sql_query, params)

        if result:
            print(f"Data inserted successfully with ID: {result}")
        else:
            print("Failed to insert data.")

        return result


def get_reference_list(session_id):
    """
    根据 session_id 从 session_file_db 表中获取所有记录，并返回指定格式的数据。
    格式: [{"filename": original_filename, "respath": respath}, ...]

    :param session_id: str，指定的会话 ID
    :return: list，包含文件名和 respath 的 JSON 列表
    """
    if DB_DEFAULT == "mongo":
        # MongoDB 查询
        print("session_id:", session_id)
        query = {"session_id": session_id}
        results = list(db.session_file.find(query))

        if results:
            print(f"MongoDB: 找到 {len(results)} 条记录")
            return [
                {
                    "filename": item["original_filename"],
                    "respath": item["respath"]
                }
                for item in results
            ]
        else:
            print("MongoDB: 未找到任何记录")
            return []

    elif DB_DEFAULT == "sqlite":
        # SQLite 查询
        sql_query = """
            SELECT original_filename, respath 
            FROM session_file 
            WHERE session_id = ?
        """
        params = (session_id,)
        results = execute_sql(sql_query, params, False)
        print("results:", results)
        print("results type :",type(results))
        if results:
            results_dict = []
            for row in results:
                # 打印每一行数据
                print(f"Processing row: {row}")
                # 将每一行转换为字典并添加到结果列表中
                results_dict.append({
                    "filename": row[0],  # original_filename 列
                    "respath": row[1]  # respath 列
                })
            print("Processed results:", results_dict)  # 打印处理后的结果
            return results_dict
        else:
            print("SQLite: 未找到任何记录")
            return []


def deletefile(file_id):
    # 判断数据库类型，执行相应的删除操作
    if DB_DEFAULT == "mongo":
        # MongoDB 删除操作
        result = db.session_file.delete_one({"file_id": file_id})
        if result.deleted_count > 0:
            print(f"MongoDB: 文件 {file_id} 删除成功")
        else:
            print(f"MongoDB: 未找到文件 {file_id}，无法删除")
        return result.deleted_count

    elif DB_DEFAULT == "sqlite":
        # SQLite 删除操作
        sql_query = """
            DELETE FROM session_file WHERE file_id = ?;
        """
        params = (file_id,)
        print("删除文件的参数",params)
        # 执行删除操作
        result = execute_sql(sql_query, params)
        if result:
            print(f"SQLite: 文件 {file_id} 删除成功")
        else:
            print(f"SQLite: 文件 {file_id} 删除失败")

        return result
    

def get_uploaded_file_address(file_id):
    # 判断数据库类型，执行相应的删除操作
    if DB_DEFAULT == "mongo":
        # MongoDB 删除操作
        result = db.session_file.find_one({"file_id": file_id})
        return result.get("address")

    elif DB_DEFAULT == "sqlite":
        # SQLite 删除操作
        sql_query = """
            SELECT address FROM session_file WHERE file_id = ?;
        """
        params = (file_id,)
        # 执行删除操作
        address = execute_sql(sql_query, params, True)
        print("上传文件的地址是",address)
        return dict(address).get("address")


def get_res_file_address(file_id):
    # 判断数据库类型，执行相应的删除操作
    if DB_DEFAULT == "mongo":
        # MongoDB 删除操作
        result = db.session_file.find_one({"file_id": file_id})
        return result.get("respath")

    elif DB_DEFAULT == "sqlite":
        # SQLite 删除操作
        sql_query = """
            SELECT respath FROM session_file WHERE file_id = ?;
        """
        params = (file_id,)
        # 执行删除操作
        address = execute_sql(sql_query, params, True)
        return dict(address).get("respath")
#【{ fileid：fileid，filename: fileName, filetype: fileType }，。。。】输入列表，更新list fileid的sessionid
def update_session_ids(files, new_session_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 批量更新操作
        file_ids = [file['file_id'] for file in files]  # 提取所有 file_id
        result = db.session_file.update_many(
            {"file_id": {"$in": file_ids}},  # 查找文件
            {"$set": {"session_id": new_session_id}}  # 更新 session_id
        )
        # 检查更新是否成功
        if result.modified_count > 0:
            return True
        else:
            return False

    elif DB_DEFAULT == "sqlite":
        # SQLite 批量更新操作
        sql_query = """
            UPDATE session_file
            SET session_id = ?
            WHERE file_id = ?;
        """
        # 准备所有更新的参数
        params = [(new_session_id, file['file_id']) for file in files]

        # 执行批量更新
        for param in params:
            result = execute_sql(sql_query, param, False)
            # 如果返回值是整数，表示受影响的行数
            if result == 0:
                return False
        return True

