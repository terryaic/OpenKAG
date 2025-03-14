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
    # 连接数据库并创建表
    from .init_db import execute_sql
    sql_query ="""
            CREATE TABLE IF NOT EXISTS kdb (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data JSON 
            );
        """
    # 调用 execute_sql 函数执行 SQL 语句
    execute_sql(sql_query, None)


def add_address_kdb(address, kdb_id):
    record = {
        "address":address,
        "kdb_id":kdb_id
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        return db.kdb.insert_one(record).inserted_id

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                INSERT INTO kdb (data) VALUES (json_insert('{}', '$.address', ?, '$.kdb_id', ?))
            """
        params = (address, kdb_id)
        result = execute_sql(sql_query, params)

        return result


def get_address(kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        return db.kdb.find_one({"kdb_id": kdb_id})

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT data FROM kdb WHERE json_extract (data, '$.kdb_id')= ?
            """
        params = (kdb_id, )
        row = execute_sql(sql_query, params, True)

        return json.loads(row[0]) if row else None



def delete_kdb(kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        db.kdb.delete_one({"kdb_id": kdb_id})
        return True

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                DELETE FROM kdb WHERE json_extract(data, '$.kdb_id') = ?
            """
        params = (kdb_id, )
        result = execute_sql(sql_query, params)
       
        return True


def delete_muilt_kdb(kdb_id_list):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        result = db.kdb.delete_many({"kdb_id": {"$in": kdb_id_list}})
        return result.deleted_count  # 返回删除的文档数量

    elif DB_DEFAULT == "sqlite":
        # 动态生成占位符
        placeholders = ', '.join(['?'] * len(kdb_id_list))

        # 构造 SQL 查询
        sql_query = f"""
            DELETE FROM kdb
            WHERE json_extract(data, '$.kdb_id') IN ({placeholders});
        """

        # 将 kdb_id_list 转换为元组形式，以便传入 SQL 查询
        params = tuple(kdb_id_list)  # tuple 形式的参数用于 IN 子句

        # 调用 execute_sql 执行删除操作
        result = execute_sql(sql_query, params)

        return True