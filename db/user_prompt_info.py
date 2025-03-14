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
    # 连接数据库并创建表
    from .init_db import execute_sql
    sql_query ="""
            CREATE TABLE IF NOT EXISTS user_prompt_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                share TEXT NOT NULL,
                date TEXT NOT NULL,
                content TEXT NOT NULL
            );
        """
    # 调用 execute_sql 函数执行 SQL 语句
    execute_sql(sql_query, None)


def get_user_prompt(user_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        results = db.prompt.find({"user_id": user_id}, {"_id": 0})

        # 将 Cursor 转换为列表
        results_list = list(results)

        return results_list

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                 SELECT * FROM user_prompt_info WHERE user_id = ?;
            """
        params = (user_id,)
        results = execute_sql(sql_query, params)

        if not results:
            return None
        
        # 转换每一行结果为字典
        dict_results = []
        for row in results:
            row_dict = dict(row)  # 将 sqlite3.Row 转换为字典
            # 判断并转换 'share' 字段的值
            if 'share' in row_dict:
                row_dict['share'] = True if row_dict['share'] == "1" else False

            dict_results.append(row_dict)  # 添加到结果列表

        return dict_results
    

def get_share_prompt():
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        results = db.prompt.find({"share": True}, {"_id": 0})

        # 将 Cursor 转换为列表
        results_list = list(results)

        return results_list

    elif DB_DEFAULT == "sqlite":
        sql_query ="""
                SELECT * FROM user_prompt_info WHERE share = 1;
            """
        results = execute_sql(sql_query, None)

        if not results:
            return None
        
        # 转换每一行结果为字典
        dict_results = []
        for row in results:
            row_dict = dict(row)  # 将 sqlite3.Row 转换为字典
            # 判断并转换 'share' 字段的值
            if 'share' in row_dict:
                row_dict['share'] = True if row_dict['share'] == "1" else False

            dict_results.append(row_dict)  # 添加到结果列表

        return dict_results



def add_user_prompt(user_id, title, share, date, content):
    record = {
        "user_id": user_id,
        "title": title, 
        "share": share, 
        "date": date,
        "content":content
    }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.prompt.update_one(
            record,  # 匹配条件
            {"$set": record},  # 更新操作
            upsert=True  # 如果没有匹配的文档则插入新的
        )
        return result
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query = """
            INSERT INTO user_prompt_info (user_id, title, share, date, content)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (record['user_id'], record['title'], record['share'], 
              record['date'], record['content'])
        rows = execute_sql(sql_query, params)

        return rows
    

def if_title_exists(title):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        print("查找的title", {"title": title})
        result = db.prompt.find_one( {"title": title} )

        if result:
            return result
        else:
            print("No matching information found.")
            return None

    elif DB_DEFAULT == "sqlite":
        sql_query = """
            SELECT * FROM user_prompt_info WHERE title = ?;
        """
        params = (title,)
        results = execute_sql(sql_query, params)

        # 判断是否有匹配的结果
        if results:
            print("Title exists.")
            return results
        else:
            print("Title does not exist.")
            return None

def get_share_type(title):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        result = db.prompt.find_one( {"title": title} )

        if result:
            share_value = result.get("share")
            return share_value
        else:
            print("No matching information found.")
            return False

    elif DB_DEFAULT == "sqlite":
        sql_query = """
            SELECT * FROM user_prompt_info WHERE title = ? 
        """
        params = (title,)
        row = execute_sql(sql_query, params, True)
        
        if row:
            share_value = bool(row[0])
            return share_value
        else:
            print("未找到匹配的 kdb_id。")
            return None

            
def get_all_prompt_title(user_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        # info = db.user.find({"information.kdb_id": kdb_id})
        result = db.prompt.find({"user_id": user_id})
        if result:
            return result
        else:
            print("No matching information found.")
            return False

    elif DB_DEFAULT == "sqlite":
        sql_query = """
            SELECT * FROM user_prompt_info WHERE user_id = ?;
        """
        params = (user_id,)
        row = execute_sql(sql_query, params)

        if row:
            return row  # 返回匹配的 title
        else:
            print("没有title")
            return None  # 如果没有匹配的 kdb_id，返回 None
        

def get_prompt_content(title):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        result = db.prompt.find_one({"title": title})
        if result:
            return result.get("content")
        else:
            print("No matching information found.")
            return False

    elif DB_DEFAULT == "sqlite":
        sql_query = """
            SELECT content  FROM user_prompt_info WHERE title = ?;
        """
        params = (title,)
        row = execute_sql(sql_query, params, True)
        
        if row:
            return row[0]  # 返回匹配的 title
        else:
            print("没有title")
            return None  # 如果没有匹配的 kdb_id，返回 None


def delete_prompt(title):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        result = db.prompt.delete_many({"title": title})
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query = """
            DELETE FROM user_prompt_info WHERE title = ?
        """
        params = (title,)
        result = execute_sql(sql_query, params)

        return result
    

def delete_muilt_prompt(prompt_title_list):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        result = db.prompt.delete_many({"title": {"$in": prompt_title_list}})
        return result

    elif DB_DEFAULT == "sqlite":
        # 动态生成占位符
        placeholders = ', '.join(['?'] * len(prompt_title_list))

        sql_query = f"""
            DELETE FROM user_prompt_info WHERE title IN ({placeholders});
        """
        
        params = tuple(prompt_title_list)
        result = execute_sql(sql_query, params)

        return result




def change_prompt_title(old_title, new_title):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        # 更新操作，修改匹配的 kdb_id 的 share 值
        result = db.prompt.update_one(
                    {"title": old_title},  # 匹配标题为 '旧标题' 的文档
                    {"$set": {"title": new_title}}  # 将 'title' 字段的值改为 '新标题'
                )
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query = """
            UPDATE user_prompt_info SET title = ? WHERE title = ?
        """
        params = (new_title, old_title)
        result = execute_sql(sql_query, params)

        return result
    

def change_prompt_share_type(title, share_type):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        # 更新操作，修改匹配的 kdb_id 的 share 值
        result = db.prompt.update_many(
                    {"title": title},  # 匹配标题为 '旧标题' 的文档
                    {"$set": {"share": share_type}}  # 将 'title' 字段的值改为 '新标题'
                )
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query = """
            UPDATE user_prompt_info SET share = ? WHERE title = ?
        """
        params = (share_type, title)
        result = execute_sql(sql_query, params)

        return result
    

def change_prompt_content(title, content):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        # 更新操作，修改匹配的 kdb_id 的 share 值
        result = db.prompt.update_many(
                    {"title": title},  # 匹配标题为 '旧标题' 的文档
                    {"$set": {"content": content}}  # 将 'title' 字段的值改为 '新标题'
                )
        return result

    elif DB_DEFAULT == "sqlite":
        sql_query = """
            UPDATE user_prompt_info SET content = ? WHERE title = ?
        """
        params = (content, title)
        result = execute_sql(sql_query, params)

        return result