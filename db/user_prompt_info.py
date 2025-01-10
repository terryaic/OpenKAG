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
            CREATE TABLE IF NOT EXISTS user_prompt_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                share TEXT NOT NULL,
                date TEXT NOT NULL,
                content TEXT NOT NULL
            );
        """)
        db.commit()
    except sqlite3.OperationalError as e:
        print(f"Error initializing SQLite database: {e}")


def get_user_prompt(user_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        results = db.prompt.find({"user_id": user_id}, {"_id": 0})

        # 将 Cursor 转换为列表
        results_list = list(results)

        return results_list

    elif DB_DEFAULT == "sqlite":
        # SQLite 查询数据
        cursor = db.cursor()
        
        # 使用参数化查询来传入 user_id
        cursor.execute("""
            SELECT * FROM user_prompt_info WHERE user_id = ?;
        """, (user_id,))

        db.commit()

        # 获取查询结果
        results = cursor.fetchall()

        if not results:
            return None
        
        # 转换每一行结果为字典
        dict_results = []
        for row in results:
            row_dict = dict(row)  # 将每个 Row 对象转换为字典
            
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
        # SQLite 查询数据
        cursor = db.cursor()

        # 使用参数化查询来传入 user_id
        cursor.execute("""
            SELECT * FROM user_prompt_info WHERE share = 1;
        """)

        db.commit()

        # 获取查询结果
        results = cursor.fetchall()

        if not results:
            return None
        
        # 转换每一行结果为字典
        dict_results = []
        for row in results:
            row_dict = dict(row)  # 将每个 Row 对象转换为字典
            
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
        # SQLite 插入数据
        cursor = db.cursor()

        print("插入数据", record)

        cursor.execute("""
            INSERT INTO user_prompt_info (user_id, title, share, date, content)
            VALUES (?, ?, ?, ?, ?)
        """, (record['user_id'], record['title'], record['share'], 
              record['date'], record['content']))
        
        # 提交事务
        db.commit()
        return cursor.lastrowid
    

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
        # SQLite 查询数据
        cursor = db.cursor()
        # 使用 JSON 查询提取指定 kdb_id 的 share 字段

        # 使用参数化查询来传入 title
        cursor.execute("""
            SELECT * FROM user_prompt_info WHERE title = ?;
        """, (title,))

        db.commit()

        # 获取所有查询结果
        results = cursor.fetchall()

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
        # SQLite 查询数据
        cursor = db.cursor()
        # 使用 JSON 查询提取指定 kdb_id 的 share 字段

        cursor.execute("""
            SELECT *  FROM user_prompt_info
            WHERE title = ? 
        """, (title,))

        db.commit()

        row = cursor.fetchone()
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
        # SQLite 查询数据
        cursor = db.cursor()
        cursor.execute("""
            SELECT *   FROM user_prompt_info
            WHERE user_id = ?;
        """, (user_id,))

        db.commit()

        row = cursor.fetchall()
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
        # SQLite 查询数据
        cursor = db.cursor()
        cursor.execute("""
            SELECT content  FROM user_prompt_info 
            WHERE title = ?;
        """, (title,))

        db.commit()

        row = cursor.fetchone()
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
        # SQLite 删除数据
        cursor = db.cursor()
        cursor.execute("DELETE FROM user_prompt_info WHERE title = ?", 
                       (title,))
        db.commit()
        return cursor.lastrowid



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
        # SQLite 删除数据
        cursor = db.cursor()
        cursor.execute("""
            UPDATE user_prompt_info
            SET title = ?
            WHERE title = ?
        """, (new_title, old_title))
        db.commit()
        return cursor.lastrowid
    

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
        # SQLite 删除数据
        cursor = db.cursor()
        cursor.execute("""
            UPDATE user_prompt_info
            SET share = ?
            WHERE title = ?
        """, (share_type, title))
        db.commit()
        return cursor.lastrowid
    

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
        # SQLite 删除数据
        cursor = db.cursor()
        cursor.execute("""
            UPDATE user_prompt_info
            SET content = ?
            WHERE title = ?
        """, (content, title))
        db.commit()
        return cursor.lastrowid
