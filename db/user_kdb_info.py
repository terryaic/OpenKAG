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
    from .init_db import execute_sql
    sql_query ="""
             CREATE TABLE IF NOT EXISTS user_kdb_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                information TEXT
            );
        """
    # 调用 execute_sql 函数执行 SQL 语句
    execute_sql(sql_query, None)


def get_user_exist(user_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        result = db.user.find_one({"user_id": user_id})
        if not result:
            return result
        return result.get("information")

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT * FROM user_kdb_info WHERE user_id = ?;
            """
        params = (user_id,)
        row = execute_sql(sql_query, params, True)

        if not row:
            return None

        # 如果查询结果是 1，表示存在该 user_id
        result = dict(row)
        info = result.get("information")
        return json.loads(info) # 将 Row 对象转换为字典
        
    
def get_user_kdb(user_id, kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        result = db.user.find_one(
            {
                "user_id": user_id,
                "information": {
                    "$elemMatch": {"kdb_id": kdb_id}
                }
            },
            {
                "information.$": 1  # 使用 `$` 只返回匹配的 `information` 数组中的一个元素
            }
        )
        return result["information"][0]

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT info.value AS information FROM user_kdb_info,
                    json_each(user_kdb_info.information) AS info
                WHERE user_kdb_info.user_id = ?
                AND json_extract(info.value, '$.kdb_id') = ?
            """
        params = (user_id,kdb_id)
        rows = execute_sql(sql_query, params)

        # 解析并输出所有匹配的信息
        if rows:
            # 将所有信息作为字典存储在列表中
            information_list = [json.loads(row["information"]) for row in rows]
            return information_list[0]
        else:
            print("未找到匹配的信息。")
            return None


def create_user_info(user_id):
    """
    info = {"user_id":  user_id,
            "information":
                [
                ]
            }
    """
    record = {
        "user_id":  user_id,
        "information": []
    }
    if DB_DEFAULT == "mongo":
        # 判断user的数据库是否已经存在
        # MongoDB 插入数据
        return db.user.insert_one(record).inserted_id

    elif DB_DEFAULT == "sqlite":
        information_json = json.dumps(record['information'])

        sql_query ="""
                INSERT INTO user_kdb_info (user_id, information) VALUES (?, ?);
            """
        params = (record['user_id'], information_json)
        result = execute_sql(sql_query, params)

        return result


def add_user_kdb(address, kdb_id, title, date, source, share, user_id, doc):
    """
    # 添加的新值
    new_entry = {"address":address,
                "kdb_id": kdb_id_uuid, "title": "新建的知识库",
                "date": kdb_date, "source": 0, "share": False,
                "user_id": user_id}
    """
    record = {
        "address":address,
        "kdb_id": kdb_id, 
        "title": title,
        "date": date, 
        "source": source, 
        "share": share,
        "user_id": user_id,
        "num_doc": doc
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.user.update_one(
            {"user_id": user_id},  # 查找指定的文档
            {"$push": {"information": record}}  # 向 info 数组中添加新值
        )
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT information FROM user_kdb_info WHERE user_id = ?;
            """
        params = (user_id,)
        row = execute_sql(sql_query, params, True)

        # 如果该用户已经有 information 字段，则更新该字段
        if row:
            existing_information = json.loads(row[0]) if row[0] else []
        else:
            existing_information = []

        # 将新的记录追加到 existing_information 中
        existing_information.append(record)

        # 将更新后的信息转为 JSON 字符串
        updated_information = json.dumps(existing_information)

        sql_query ="""
                UPDATE user_kdb_info SET information = ? WHERE user_id = ?;
            """
        params = (updated_information, user_id)
        row = execute_sql(sql_query, params, True)

        return row


def get_share_type(user_id, kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        # info = db.user.find({"information.kdb_id": kdb_id})
        result = db.user.find_one(
            {
                "user_id": user_id,
                "information": {
                    "$elemMatch": {"kdb_id": kdb_id}
                }
            },
            {
                "information.$": 1  # 使用 `$` 只返回匹配的 `information` 数组中的一个元素
            }
        )
        if result and "information" in result:
            share_value = result["information"][0].get("share")
            return share_value
        else:
            print("No matching information found.")
            return False

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT json_extract(info.value, '$.share')
                FROM user_kdb_info,
                json_each(user_kdb_info.information) AS info
                WHERE user_id = ? 
                AND json_extract(info.value, '$.kdb_id') = ?;
            """
        params = (user_id, kdb_id)
        row = execute_sql(sql_query, params, True)
        
        if row:
            share_value = bool(row[0])
            return share_value
        else:
            print("未找到匹配的 kdb_id。")
            return None

            
def get_kdb_title(kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        # info = db.user.find({"information.kdb_id": kdb_id})
        result = db.user.find_one(
            {
                "information": {
                    "$elemMatch": {"kdb_id": kdb_id}
                }
            },
            {
                "information.$": 1  # 使用 `$` 只返回匹配的 `information` 数组中的一个元素
            }
        )
        if result and "information" in result:
            title = result["information"][0].get("title")
            return title
        else:
            print("No matching information found.")
            return False

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT json_extract(arr.value, '$.title') AS title
            FROM user_kdb_info,
            json_each(user_kdb_info.information) AS arr
            WHERE json_extract(arr.value, '$.kdb_id') = ?;
            """
        params = (kdb_id, )
        row = execute_sql(sql_query, params, True)

        if row:
            return row[0]  # 返回匹配的 title
        else:
            print("没有title")
            return None  # 如果没有匹配的 kdb_id，返回 None
        

def get_user_id(kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        # info = db.user.find({"information.kdb_id": kdb_id})
        result = db.user.find_one(
            {
                "information": {
                    "$elemMatch": {"kdb_id": kdb_id}
                }
            },
            {
                "information.$": 1  # 使用 `$` 只返回匹配的 `information` 数组中的一个元素
            }
        )
        if result and "information" in result:
            user_id = result["information"][0].get("user_id")
            return user_id
        else:
            print("No matching information found.")
            return False

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT json_extract(arr.value, '$.user_id') AS user_id
            FROM user_kdb_info,
            json_each(user_kdb_info.information) AS arr
            WHERE json_extract(arr.value, '$.kdb_id') = ?;
            """
        params = (kdb_id, )
        row = execute_sql(sql_query, params, True)

        if row:
            return row[0]  # 返回匹配的 title
        else:
            print("没有title")
            return None  # 如果没有匹配的 kdb_id，返回 None
    

def get_kdb_id(user_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        result = db.user.find_one(
            {
                "user_id": user_id,
            }
        )
        kdb_id = []

        if result and "information" in result:
            info = result["information"]
            for i in info:
                a = {}
                a["kdb_id"] = i["kdb_id"]
                a["title"] = i["title"]
                a["share"] = i["share"]
                kdb_id.append(a)
            return kdb_id
        else:
            print("No matching information found.")
            return kdb_id

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT 
                json_extract(arr.value, '$.title') AS title,
                json_extract(arr.value, '$.kdb_id') AS kdb_id,
                json_extract(arr.value, '$.share') AS share
                FROM user_kdb_info, 
                json_each(user_kdb_info.information) AS arr
                WHERE user_kdb_info.user_id = ?;
            """
        params = (user_id, )
        kdb_info = execute_sql(sql_query, params)

        # 直接将查询结果转换为字典格式
        titles = [{"title": row[0], "kdb_id": row[1], "share": row[2]} for row in kdb_info]
        return titles


def delete_kdb(user_id, kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        result = db.user.update_one(
            {"user_id": user_id},  # 查找 user_id 为 123 的文档
            {"$pull": {"information": {"kdb_id": kdb_id}}}  # 从 info 数组中删除包含 user_id 为 123 的元素
        )
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT information FROM user_kdb_info WHERE user_id = ?
            """
        params = (user_id, )
        row = execute_sql(sql_query, params, True)

        if row:
            # 解析 information 字段的 JSON 数据
            information = json.loads(row[0])  # 假设是一个列表
            
            # 删除信息数组中 kdb_id 匹配的元素
            information = [item for item in information if item.get('kdb_id') != kdb_id]
            
            # 将修改后的数组转换回 JSON 字符串
            updated_information = json.dumps(information)

            sql_query ="""
                    UPDATE user_kdb_info SET information = ? WHERE user_id = ?;
                """
            params = (updated_information, user_id)
            row = execute_sql(sql_query, params)
            if row:
                return True
            else:
                return False
        else:
            print(f"No data found for user_id {user_id}.")
            return False
        

def delete_muilt_kdb(user_id, kdb_id_list):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        result = db.user.update_one(
            {"user_id": user_id},  # 查找 user_id 为 123 的文档
            {"$pull": {"information": {"kdb_id": {"$in": kdb_id_list}}}}  # 从数组中删除多个符合条件的元素
        )
        return result.modified_count  # 返回修改的文档数

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT information FROM user_kdb_info WHERE user_id = ?
            """
        params = (user_id, )
        row = execute_sql(sql_query, params, True)

        if row:
            # 解析 information 字段的 JSON 数据
            information = json.loads(row[0])  # 假设是一个列表
            
            # 删除信息数组中 kdb_id 匹配的元素
            information = [item for item in information if item.get('kdb_id') not in kdb_id_list]
            
            # 将修改后的数组转换回 JSON 字符串
            updated_information = json.dumps(information)

            sql_query ="""
                    UPDATE user_kdb_info SET information = ? WHERE user_id = ?;
                """
            params = (updated_information, user_id)
            row = execute_sql(sql_query, params)
            if row:
                return True
            else:
                return False
        else:
            print(f"No data found for user_id {user_id}.")
            return False


def change_kdb_title(user_id, kdb_id, new_title):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        # 更新操作，修改匹配的 kdb_id 的 share 值
        result = db.user.update_one(
            {
                "user_id": user_id,
                "information.kdb_id": kdb_id
            },
            {
                "$set": {
                    "information.$.title": new_title
                }
            }
        )
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT information FROM user_kdb_info WHERE user_id = ?
            """
        params = (user_id, )
        row = execute_sql(sql_query, params, True)

        if row:
            # 解析 information 字段的 JSON 数据
            information = json.loads(row[0])  # 假设是一个包含字典的数组
            
            # 遍历 information 数组，找到匹配的 kdb_id 并更新 title
            for item in information:
                if item.get('kdb_id') == kdb_id:
                    item['title'] = new_title  # 更新 title 字段
                    break
            
            # 将更新后的信息转换为 JSON 字符串
            updated_information = json.dumps(information)

            sql_query ="""
                    UPDATE user_kdb_info SET information = ? WHERE user_id = ?;
                """
            params = (updated_information, user_id)
            row = execute_sql(sql_query, params)
            
            if row:
                return True
            else:
                return False
        else:
            print(f"No data found for user_id {user_id}.")
            return False
    

def change_kdb_share(user_id, kdb_id, share_type):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        # 更新操作，修改匹配的 kdb_id 的 share 值
        result = db.user.update_one(
            {
                "user_id": user_id,
                "information.kdb_id": kdb_id
            },
            {
                "$set": {
                    "information.$.share": share_type
                }
            }
        )
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT information FROM user_kdb_info WHERE user_id = ?;
            """
        params = (user_id,)
        row = execute_sql(sql_query, params, True)

        if row:
            # 解析 information 字段的 JSON 数据
            information = json.loads(row[0])  # 假设是一个包含字典的数组
            
            # 遍历 information 数组，找到匹配的 kdb_id 并更新 title
            for item in information:
                if item.get('kdb_id') == kdb_id:
                    item['share'] = share_type  # 更新 title 字段
                    break
            
            # 将更新后的信息转换为 JSON 字符串
            updated_information = json.dumps(information)

            sql_query ="""
                    UPDATE user_kdb_info SET information = ? WHERE user_id = ?;
                """
            params = (updated_information, user_id)
            row = execute_sql(sql_query, params)

            if row:
                return True
            else:
                return False
        else:
            print(f"No data found for user_id {user_id}.")
            return False
    

def change_kdb_source(user_id, kdb_id, new_source):
    if DB_DEFAULT == "mongo":
        # 更新操作，修改匹配的 kdb_id 的 share 值
        print("上传的文件数量是：",new_source)
        result = db.user.update_one(
            {
                "user_id": user_id,
                "information.kdb_id": kdb_id
            },
            {
                "$inc": {
                    "information.$.source": new_source  # 使用 $ 来定位匹配的元素
                }
            }
        )
        
        if result.matched_count == 0:
            return {"message": "No matching user or kdb_id found"}

        if result.modified_count == 0:
            return {"message": "No update performed, source field might be unchanged"}

        return {"message": "Update successful", "modified_count": result.modified_count}

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                 SELECT information FROM user_kdb_info WHERE user_id = ?;
            """
        params = (user_id,)
        row = execute_sql(sql_query, params, True)

        if row:
            information = json.loads(row[0])  # 将 JSON 解析为 Python 数据结构
            # 遍历列表，找到匹配的 `kdb_id` 并更新 `source` 值
            for item in information:
                if item.get("kdb_id") == kdb_id:
                    item["source"] = item.get("source", 0) + new_source  # 增加 `source` 的值
                    break
            
            sql_query ="""
                    UPDATE user_kdb_info SET information = ? WHERE user_id = ?;
                """
            params = (json.dumps(information), user_id)
            row = execute_sql(sql_query, params)

            if row:
                return True
            else:
                return False
        else:
            return False
        

def change_kdb_doc(user_id, kdb_id, new_doc):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        # 更新操作，修改匹配的 kdb_id 的 share 值
        result = db.user.update_one(
            {
                "user_id": user_id,
                "information.kdb_id": kdb_id
            },
            {
                "$inc": {
                    "information.$.num_doc": new_doc  # 使用 $ 来定位匹配的元素
                }
            }
        )
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT information FROM user_kdb_info WHERE user_id = ?;
            """
        params = (user_id, )
        row = execute_sql(sql_query, params, True)

        if row:
            information = json.loads(row[0])  # 将 JSON 解析为 Python 数据结构
            # 遍历列表，找到匹配的 `kdb_id` 并更新 `source` 值
            for item in information:
                if item.get("kdb_id") == kdb_id:
                    item["num_doc"] = item.get("num_doc", 0) + new_doc  # 增加 `source` 的值
                    break
            
            sql_query ="""
                    UPDATE user_kdb_info SET information = ? WHERE user_id = ?;
                """
            params = (json.dumps(information), user_id)
            row = execute_sql(sql_query, params, True)

            if row:
                return True
            else:
                return False
        else:
            return False
        

def get_kdb_doc(kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        # info = db.user.find({"information.kdb_id": kdb_id})
        result = db.user.find_one(
            {
                "information": {
                    "$elemMatch": {"kdb_id": kdb_id}
                }
            },
            {
                "information.$": 1  # 使用 `$` 只返回匹配的 `information` 数组中的一个元素
            }
        )
        if result and "information" in result:
            num_doc = result["information"][0].get("num_doc")
            return num_doc
        else:
            print("No matching information found.")
            return False

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT json_extract(arr.value, '$.num_doc') AS num_doc
                FROM user_kdb_info,
                json_each(user_kdb_info.information) AS arr
                WHERE json_extract(arr.value, '$.kdb_id') = ?;
            """
        params = (kdb_id,)
        row = execute_sql(sql_query, params, True)

        if row:
            return row[0]  # 返回匹配的 title
        else:
            print("没有num_doc")
            return None  # 如果没有匹配的 kdb_id，返回 None