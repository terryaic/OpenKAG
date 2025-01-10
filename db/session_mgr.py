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

    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    try:
        db = sqlite3.connect(db_path, check_same_thread= False)
        cursor = db.cursor()
        # 确保表存在
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                data JSON  -- 使用 JSON 类型存储整个 JSON 对象
            )
        """)
        db.commit()
    except sqlite3.OperationalError as e:
        print(f"Error initializing database: {e}")

def create_session(user, session_id, title="",kdb_id=None):
    create_time = time.time()
    data={"user": user, "session_id": session_id, "title": title, "create_time": create_time, "update_time": create_time,"kdb_id":kdb_id}
    if DB_DEFAULT == "mongo":
        return db.session.insert_one(data).inserted_id
    elif DB_DEFAULT == "sqlite":
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO session (data)
             VALUES (json_insert('{}', '$.user', ?, '$.session_id', ?, '$.title', ?, '$.create_time', ?, '$.update_time', ?, '$.kdb_id', ?))
        """, (user, session_id, title, create_time, create_time,kdb_id))
        db.commit()
        return cursor.lastrowid


import json
def list_session(user):
    if DB_DEFAULT == "mongo":
        return db.session.find({"user": user}).sort("create_time", pymongo.DESCENDING).to_list()
    elif DB_DEFAULT == "sqlite":
        cursor = db.cursor()

        # 使用 json_extract 从 SQLite 的 JSON 数据列中提取 user 字段进行查询
        cursor.execute(
            "SELECT data FROM session WHERE json_extract(data, '$.user') = ? ORDER BY json_extract(data, '$.create_time') DESC",
            (user,))

        rows = cursor.fetchall()  # 获取所有符合条件的行

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
        cursor = db.cursor()
        cursor.execute("SELECT data FROM session WHERE json_extract (data, '$.session_id')= ?", (session_id,))

        row = cursor.fetchone()  # 将查询结果赋值给 rows，避免重复 fetchall 调用
        return json.loads(row[0]) if row else None



def update_session(session):
    if DB_DEFAULT == "mongo":
        query = {"session_id": session['session_id']}
        new_value = {"$set": {"update_time": time.time()}}
        db.session.update_one(query, new_value)
    elif DB_DEFAULT == "sqlite":
        cursor = db.cursor()
        cursor.execute("""
            UPDATE session
            SET data = json_replace(data, '$.update_time', ?)
            WHERE json_extract(data, '$.session_id') = ?
        """, (time.time(), session['session_id']))
        db.commit()


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
            cursor = db.cursor()
            cursor.execute("""
                DELETE FROM session
                WHERE json_extract(data, '$.session_id') = ?
            """, (session,))
            db.commit()
            # 判断删除是否成功
            if cursor.rowcount > 0:
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
        cursor = db.cursor()
        cursor.execute("""
            SELECT json_extract(data, '$.kdb_id') 
            FROM session 
            WHERE json_extract(data, '$.session_id') = ?
        """, (session_id,))
        result = cursor.fetchone()
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
        cursor = db.cursor()
        cursor.execute("""
            UPDATE session 
            SET data = json_set(data, '$.kdb_id', ?)
            WHERE json_extract(data, '$.session_id') = ?
        """, (new_kdb_id, session_id))
        db.commit()
        if cursor.rowcount > 0:
            return True  # 成功更新
        else:
            return False  # 未找到匹配的 session_id


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
