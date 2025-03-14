import json
import os
import time
import pymongo
from pymongo import DESCENDING,ASCENDING
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
            CREATE TABLE IF NOT EXISTS session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data JSON
            );
        """
    # 调用 execute_sql 函数执行 SQL 语句
    execute_sql(sql_query, None)


def create_session(user, session_id, title='' ,reference="",kdb_id=None, extra_info=None):
    print("创建session")
    create_time = time.time()
    data={"user": user, "session_id": session_id,"reference":reference, "title": title, 
          "create_time": create_time, "update_time": create_time,"kdb_id":kdb_id, "extra_info":extra_info}
    if DB_DEFAULT == "mongo":
        return db.session.insert_one(data).inserted_id
    elif DB_DEFAULT == "sqlite":
        sql_query = """
            INSERT INTO session (data)
            VALUES (
                json_insert('{}', 
                            '$.user', ?, 
                            '$.session_id', ?, 
                            '$.reference', ?, 
                            '$.title', ?, 
                            '$.create_time', ?, 
                            '$.update_time', ?, 
                            '$.kdb_id', ?,
                            '$.extra_info', ?

                )
            )
        """
        params = (user, session_id, reference, title, create_time, create_time, kdb_id, extra_info)
        result = execute_sql(sql_query, params)

        return result


import json
def list_session(user):
    if DB_DEFAULT == "mongo":
        result = db.session.find(
            {"user": user},
            {"_id": 0}  # 使用 projection 排除 "_id" 字段
        ).sort("create_time", DESCENDING).to_list()

        return result
    elif DB_DEFAULT == "sqlite":
        sql_query = """
            SELECT data FROM session WHERE json_extract(data, '$.user') = ? 
            ORDER BY json_extract(data, '$.create_time') DESC
        """
        params = (user,)
        rows = execute_sql(sql_query, params)
        
        result = []
        for row in rows:
            # row[0] 这里是存储 JSON 数据的字段（data），需要将其解析为字典
            session_data = json.loads(row[0])  # 将 JSON 字符串转换为字典
            result.append(session_data)

        return result
    
def list_session_with_extra(user, extra):
    if DB_DEFAULT == "mongo":
        result = db.session.find(
            {"user": user},
            {"_id": 0},  # 使用 projection 排除 "_id" 字段
            {"extra_info": extra}
        ).sort("create_time", ASCENDING).to_list()

        return result
    elif DB_DEFAULT == "sqlite":
        sql_query = """
            SELECT data FROM session WHERE json_extract(data, '$.user') = ? and json_extract(data, '$.extra_info') = ?
            ORDER BY json_extract(data, '$.create_time') ASC
        """
        params = (user, extra, )
        rows = execute_sql(sql_query, params)
        
        result = []
        for row in rows:
            # row[0] 这里是存储 JSON 数据的字段（data），需要将其解析为字典
            session_data = json.loads(row[0])  # 将 JSON 字符串转换为字典
            result.append(session_data)

        return result


def get_session(session_id):
    if DB_DEFAULT == "mongo":
        return db.session.find_one({"session_id": session_id})
    elif DB_DEFAULT == "sqlite":
        sql_query = """
            SELECT data FROM session WHERE json_extract (data, '$.session_id')= ?
        """
        params = (session_id,)
        row = execute_sql(sql_query, params, True)
        
        return json.loads(row[0]) if row else None



def update_session(session):
    if DB_DEFAULT == "mongo":
        query = {"session_id": session['session_id']}
        new_value = {"$set": {"update_time": time.time()}}
        db.session.update_one(query, new_value)
    elif DB_DEFAULT == "sqlite":
        sql_query = """
            UPDATE session
            SET data = json_replace(data, '$.update_time', ?)
            WHERE json_extract(data, '$.session_id') = ?
        """
        params = (time.time(), session['session_id'])
        row = execute_sql(sql_query, params)
        return row

def get_reference_list(session_id):
    """
    根据 session_id 查询 reference 字段，如果存在且非空，返回其列表形式。

    :param session_id: str，指定的会话 ID
    :return: list，返回 reference 列表或空列表
    """
    if DB_DEFAULT == "mongo":
        # MongoDB 查询
        print('session_id',session_id)
        query = {"session_id": session_id}
        result = db.session.find_one(query)
        print("result",result)

        if result and "reference" in result and result["reference"]:
            reference_list = result["reference"]
            if isinstance(reference_list, list):
                return reference_list
            else:
                print("MongoDB: reference 字段不是列表，返回空列表")
                return []
        else:
            print("MongoDB: reference 字段为空或不存在")
            return []

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT json_extract(data, '$.reference') 
                FROM session 
                WHERE json_extract(data, '$.session_id') = ?
            """
        params = (session_id, )
        result = execute_sql(sql_query, params, True)

        if result and result[0]:
            try:
                reference_list = json.loads(result[0])  # 尝试解析为列表
                if isinstance(reference_list, list):
                    return reference_list
                else:
                    print("SQLite: reference 字段不是列表，返回空列表")
                    return []
            except json.JSONDecodeError:
                print("SQLite: reference 字段不是合法的 JSON 格式")
                return []
        else:
            print("SQLite: reference 字段为空或不存在")
            return []

    else:
        print("未知数据库类型")
        return []


def delete_session(session):
    try:
        if DB_DEFAULT == "mongo":
            index = {"session_id": session}
            result = db.session.delete_one(index)
            # 判断删除是否成功
            if result.deleted_count > 0:
                return True  # 删除成功
            else:
                return False  # 删除失败，未找到匹配项
        elif DB_DEFAULT == "sqlite":
            sql_query ="""
                    DELETE FROM session WHERE json_extract(data, '$.session_id') = ?
                """
            params = (session, )
            result = execute_sql(sql_query, params)
            print("删除session",result)
            # 判断删除是否成功
            if result > 0:
                return True  # 删除成功
            else:
                return False  # 删除失败，未找到匹配项
    except Exception as e:
        print(f"Error while deleting session: {e}")
        return False  # 出现错误时返回失败

def get_current_kdb(session_id):
    if DB_DEFAULT == "mongo":
        # 在 MongoDB 中查找 session_id 对应的记录
        session_data = db.session.find_one({"session_id": session_id})
        if session_data:
            return session_data.get("kdb_id", None)
        else:
            return None

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT json_extract(data, '$.kdb_id') FROM session 
                WHERE json_extract(data, '$.session_id') = ?
            """
        params = (session_id, )
        result = execute_sql(sql_query, params, True)

        if result:
            return result[0]
        else:
            return None


def change_kdb(session_id, new_kdb_id):
    if DB_DEFAULT == "mongo":
        # 在 MongoDB 中更新 session 中的 kdb_id
        result = db.session.update_one(
            {"session_id": session_id},  # 查找对应的 session_id
            {"$set": {"kdb_id": new_kdb_id}}  # 更新 kdb_id 字段
        )
        if result.matched_count > 0:
            return True  # 成功更新
        else:
            return False  # 未找到匹配的 session_id

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                UPDATE session SET data = json_set(data, '$.kdb_id', ?)
                WHERE json_extract(data, '$.session_id') = ?
            """
        params = (new_kdb_id, session_id)
        result = execute_sql(sql_query, params, True)
        
        if result:
            return True  # 成功更新
        else:
            return False  # 未找到匹配的 session_id
        

def change_title(session_id, new_title):
    if DB_DEFAULT == "mongo":
        # 在 MongoDB 中更新 session 中的 kdb_id
        result = db.session.update_one(
            {"session_id": session_id},  # 查找对应的 session_id
            {"$set": {"title": new_title}}  # 更新 kdb_id 字段
        )
        if result.matched_count > 0:
            return True  # 成功更新
        else:
            return False  # 未找到匹配的 session_id

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                UPDATE session SET data = json_set(data, '$.title', ?)
                WHERE json_extract(data, '$.session_id') = ?
            """
        params = (new_title, session_id)
        try:
            result = execute_sql(sql_query, params, True)
            return True  # 成功更新
        except:
            return False  # 成功更新



if __name__ == "__main__":
    # # 示例 session_id，用于测试
    # session_id_to_find = "b351f6a28a984e86b707372dd9fd30c1"
    #
    # # 查找指定 session_id 的数据
    # session_data = get_session(session_id_to_find)
    #
    # # 打印结果
    # if session_data:
    #     # 转换为列表形式
    #     session_list = [session_data]
    #     print("找到的 session 数据（列表形式）:")
    #     print(session_list)
    # else:
    #     print(f"未找到 session_id 为 {session_id_to_find} 的数据。")

    session_id_to_find = "a5a8a4c3b35c45c69ec73b57f0be2d6e"
    #change_kdb("a5a8a4c3b35c45c69ec73b57f0be2d6e",1)
    # 查找指定 session_id 对应的 kdb_id
    kdb_id = get_current_kdb(session_id_to_find)

    # 打印结果
    if kdb_id:
        print(f"找到的 kdb_id: {kdb_id}")
    else:
        print(f"未找到 session_id 为 {session_id_to_find} 的 kdb_id。")