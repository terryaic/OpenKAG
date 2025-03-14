import json
import os
import time
import pymongo
import sqlite3
import json
from settings import MONGODB_HOST, MONGODB_PORT, DB_DEFAULT, SQLITE_DB_PATH,DBNAME
current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQLITE_DB_PATH)

# MongoDB 和 SQLite 的配置根据 DB_DEFAULT 进行选择
if DB_DEFAULT == "mongo":
    client = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
    db = client[DBNAME]
    collection = db.doc  # 选择集合

    # 仅更新不存在 session_id 字段的文档
    result = collection.update_many(
        {"session_id": {"$exists": False}},  # 条件：session_id 不存在
        {"$set": {"session_id": None}}       # 添加字段 session_id 并初始化为 null
    )

    print(f"Matched {result.matched_count} documents, Modified {result.modified_count} documents")

elif DB_DEFAULT == "sqlite":
    # 连接数据库并创建表
    from .init_db import execute_sql
    sql_query ="""
            CREATE TABLE IF NOT EXISTS doc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                kdb_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                file_name TEXT NOT NULL
            );
        """
    # 调用 execute_sql 函数执行 SQL 语句
    execute_sql(sql_query, None)

    def column_exists(table_name, column_name):
        sql_check_column = f"PRAGMA table_info({table_name});"
        columns = execute_sql(sql_check_column, None)  # 假设 execute_sql 返回查询结果
        return any(col[1] == column_name for col in columns)  # 列名通常在结果的第二列

    # 检查列是否存在，避免重复添加
    if not column_exists("doc", "session_id"):
        sql_add_column = """
            ALTER TABLE doc
            ADD COLUMN session_id TEXT;
        """
        execute_sql(sql_add_column, None)
    else:
        print("Column 'session_id' already exists.")



def add_doc_id(user_id, kdb_id, doc_id, file_name, session_id):
    record = {
        "user_id": user_id,
        "kdb_id": kdb_id,
        "doc_id": doc_id,
        "file_name": file_name,
        "session_id":session_id
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.doc.update_one(
            record,  # 匹配条件
            {"$set": record},  # 更新操作
            upsert=True  # 如果没有匹配的文档则插入新的
        )
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                INSERT INTO doc (user_id, kdb_id, doc_id, file_name, session_id) \
                        VALUES (?, ?, ?, ?, ?)
            """
        params = (user_id, kdb_id, doc_id, file_name, session_id)
        result = execute_sql(sql_query, params)

        return result



def delete_doc_id(kdb_id, file_name):
    record = {
        "kdb_id": kdb_id,
        "file_name": file_name
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.doc.delete_one(record)
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                DELETE FROM doc WHERE kdb_id = ? AND file_name = ?;
            """
        params = (kdb_id,file_name)
        result = execute_sql(sql_query, params)
        
        return result
    

def delete_doc_id_session(session_id, file_name):
    record = {
        "session_id": session_id,
        "file_name": file_name
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.doc.delete_one(record)
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                DELETE FROM doc WHERE session_id = ? AND file_name = ?;
            """
        params = (session_id,file_name)
        result = execute_sql(sql_query, params)
        
        return result
    

def delete_user_kdb_doc(kdb_id):
    record = {
        "kdb_id": kdb_id
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.doc.delete_many(record)
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                DELETE FROM doc WHERE kdb_id = ?;
            """
        params = (kdb_id,)
        result = execute_sql(sql_query, params)
        
        return result
    

def delete_muilt_user_kdb_doc(kdb_id_list):
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.doc.delete_many({"kdb_id": {"$in": kdb_id_list}})
        return result.deleted_count  # 返回删除的文档数量

    elif DB_DEFAULT == "sqlite":
        # 动态生成占位符
        placeholders = ', '.join(['?'] * len(kdb_id_list))

        sql_query = f"""
            DELETE FROM doc WHERE kdb_id IN ({placeholders});
        """
      
        # Ensure the list of kdb_ids is passed correctly as parameters
        params = tuple(kdb_id_list)

        print("doc多个删除的值是:",params)
        
        row = execute_sql(sql_query, params)
    

def get_file_name(if_kdb, id, doc_id):
    key = "kdb_id" if if_kdb else "session_id"

    if DB_DEFAULT == "mongo":
        record = {
            key: id,
            "doc_id": doc_id
        }

        # MongoDB 插入数据
        result = db.doc.find_one(record)
        print("数据库茶找到的数据：",result)
        if result:
            file_name = result.get("file_name")
            user_id = result.get("user_id")
            return file_name, user_id  # 如果找到匹配的文档，返回文档
        else:
            return None, {"message": "No document found with the specified kdb_id and doc_id"}  # 如果未找到


    elif DB_DEFAULT == "sqlite":
        sql_query =f"""
                SELECT user_id, file_name FROM doc WHERE {key} = ? AND doc_id = ?;
            """
        params = (id, doc_id)
        file_name_tuple = execute_sql(sql_query, params, fetchone=True)

        if file_name_tuple:
            user_id = file_name_tuple[0]  # 提取元组中的第一个元素（file_name）
            file_name = file_name_tuple[1]
            return file_name, user_id
        else:
            return None, {"message": "No document found with the specified kdb_id and doc_id"}  # 如果未找到


def get_num_session(session_id):
    if DB_DEFAULT == "mongo":
        count = db.doc.count_documents({"session_id": session_id})
        return count

    elif DB_DEFAULT == "sqlite":
        # SQLite 查询
        sql_query = """
            SELECT COUNT(*) FROM doc WHERE session_id = ?;
        """
        params = (session_id,)
        count_tuple = execute_sql(sql_query, params, fetchone=True)
        return count_tuple[0] if count_tuple else 0

        