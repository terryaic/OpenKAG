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

elif DB_DEFAULT == "sqlite":
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # 连接数据库并创建表
    try:
        db = sqlite3.connect(db_path, check_same_thread= False)
        # 设置 row_factory 为 sqlite3.Row 以便返回字典格式的查询结果
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                kdb_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                file_name TEXT NOT NULL
            );
        """)
        db.commit()
    except sqlite3.OperationalError as e:
        print(f"Error initializing SQLite database: {e}")


def add_doc_id(user_id, kdb_id, doc_id, file_name):
    record = {
        "user_id": user_id,
        "kdb_id": kdb_id,
        "doc_id": doc_id,
        "file_name": file_name
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
        # SQLite 插入数据
        cursor = db.cursor()
        # 查询现有的 information 字段值

        # 插入数据
        cursor.execute("INSERT INTO doc (user_id, kdb_id, doc_id, file_name) \
                        VALUES (?, ?, ?, ?)", (user_id, kdb_id, doc_id, file_name))
        
        # 提交事务
        db.commit()

        return cursor.lastrowid



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
        # SQLite 插入数据
        cursor = db.cursor()
        # 查询现有的 information 字段值
        # 插入数据
        print("删除doc", record)
        cursor.execute("DELETE FROM doc \
                    WHERE kdb_id = ? AND file_name = ?;", (kdb_id, file_name,))
        
        # 提交事务
        db.commit()
        
        return cursor.lastrowid
    

def delete_user_kdb_doc(kdb_id):
    record = {
        "kdb_id": kdb_id
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.doc.delete_many(record)
        return result

    elif DB_DEFAULT == "sqlite":
        # SQLite 插入数据
        cursor = db.cursor()
        # 查询现有的 information 字段值
        # 插入数据
        print("删除doc", record)
        cursor.execute("DELETE FROM doc \
                    WHERE kdb_id = ?;", (kdb_id,))
        
        # 提交事务
        db.commit()
        
        return cursor.lastrowid
    

def get_file_name(kdb_id, doc_id):
    record = {
        "kdb_id": kdb_id,
        "doc_id": doc_id
    }
    if DB_DEFAULT == "mongo":
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
        # SQLite 插入数据
        cursor = db.cursor()
        # 查询现有的 information 字段值
        # 插入数据
        cursor.execute("SELECT user_id, file_name FROM doc \
                       WHERE kdb_id = ? AND doc_id = ?", (kdb_id, doc_id,))
        
        # 提交事务
        db.commit()

        file_name_tuple = cursor.fetchone()


        if file_name_tuple:
            user_id = file_name_tuple[0]  # 提取元组中的第一个元素（file_name）
            file_name = file_name_tuple[1]
            return file_name, user_id
        else:
            return None, {"message": "No document found with the specified kdb_id and doc_id"}  # 如果未找到
