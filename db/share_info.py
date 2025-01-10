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
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS share_kdb_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                share_type TEXT,
                information TEXT
            );
        """)
        db.commit()
    except sqlite3.OperationalError as e:
        print(f"Error initializing SQLite database: {e}")


def get_share_exist():
    if DB_DEFAULT == "mongo":
        # MongoDB 查询
        result = db.share.find_one({"share_type": "share"})
        if not result:
            return result
        return result.get("information")



    elif DB_DEFAULT == "sqlite":
        # SQLite 查询数据
        cursor = db.cursor()

        # 使用参数化查询来传入 user_id
        cursor.execute("""
            SELECT * FROM share_kdb_info WHERE share_type = ?;
        """, ("share",))

        db.commit()

        # 获取查询结果
        row = cursor.fetchone()

        if not row:
            return None

        # 如果查询结果是 1，表示存在该 user_id
        result = dict(row)
        info = result.get("information")
        return json.loads(info) # 将 Row 对象转换为字典

def create_share_info():
    """
    info = {"information":[]
            }
    """
    record = {
            "share_type": "share",
            "information": []
        }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        return db.share.insert_one(record).inserted_id

    elif DB_DEFAULT == "sqlite":
        # SQLite 插入数据
        cursor = db.cursor()

         # 将包含字典的数组转换为 JSON 格式的字符串
        information_json = json.dumps(record['information'])

        # 插入数据
        cursor.execute("""
            INSERT INTO share_kdb_info (share_type, information)
            VALUES (?, ?);
        """, (record['share_type'], information_json))

        # 提交事务
        db.commit()

        # 获取插入的记录的 ID
        share_type = cursor.lastrowid
        
        return share_type

def add_kdb(info):
    """
    # 添加的新值
    new_entry = {"address":address,
                "kdb_id": kdb_id_uuid, "title": "新建的知识库",
                "date": kdb_date, "source": 0, "share": False,
                "user_id": user_id}
    """
    # record = {
    #     "address":address,
    #     "kdb_id": kdb_id, 
    #     "title": title,
    #     "date": date, 
    #     "source": source, 
    #     "share": share,
    #     "user_id": user_id
    # }
    if DB_DEFAULT == "mongo":
        # MongoDB 插入数据
        result = db.share.update_one(
            {"share_type": "share"},  # 查找指定的文档
            {"$push": {"information": info}}  # 向 info 数组中添加新值
        )
        return result

    elif DB_DEFAULT == "sqlite":
        # SQLite 插入数据
        cursor = db.cursor()

        cursor.execute("""
            SELECT information FROM share_kdb_info WHERE share_type = ?;
        """, ("share",))

        # 获取查询结果
        row = cursor.fetchone()

        # 如果该用户已经有 information 字段，则更新该字段
        if row:
            existing_information = json.loads(row[0]) if row[0] else []
        else:
            existing_information = []
        # 将新的记录追加到 existing_information 中
        existing_information.append(info)

        # 将更新后的信息转为 JSON 字符串
        updated_information = json.dumps(existing_information)

        # 更新 information 字段
        cursor.execute("""
            UPDATE share_kdb_info
            SET information = ?
            WHERE share_type = ?;
        """, (updated_information, "share"))

        db.commit()
        return cursor.lastrowid

def delete_kdb(kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        result = db.share.update_one(
            {"share_type": "share"},  # 查找 user_id 为 123 的文档
            {"$pull": {"information": {"kdb_id": kdb_id}}}  # 从 info 数组中删除包含 user_id 为 123 的元素
        )
        return result

    elif DB_DEFAULT == "sqlite":
        # SQLite 删除数据
        cursor = db.cursor()
        # 查询出目标数据
        cursor.execute("""
            SELECT information 
            FROM share_kdb_info 
            WHERE share_type = 'share';
        """)
        row = cursor.fetchone()

        if row:
            information = json.loads(row[0])  # 将 JSON 数据解析成 Python 列表
            # 删除匹配的 kdb_id 的对象
            information = [item for item in information if item.get("kdb_id") != kdb_id]
            
            # 将修改后的信息更新回数据库
            cursor.execute("""
                UPDATE share_kdb_info 
                SET information = json(?) 
                WHERE share_type = 'share';
            """, (json.dumps(information),))

            db.commit()
            return True
        else:
            print("未找到匹配的数据。")
            return False

def change_kdb_title(kdb_id, new_title):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        # 更新操作，修改匹配的 kdb_id 的 share 值
        result = db.share.update_one(
            {
                "share_type": "share",
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
        # SQLite 删除数据
        cursor = db.cursor()
        cursor.execute("SELECT information FROM share_kdb_info WHERE share_type = 'share';")
        row = cursor.fetchone()

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
            
            # 更新数据库中的 information 字段
            cursor.execute("""
                UPDATE share_kdb_info
                SET information = ?
                WHERE share_type = 'share';
            """, (updated_information,))
            
            # 提交事务
            db.commit()
            return True
        else:
            return False

def change_kdb_source(kdb_id, new_source):
    if DB_DEFAULT == "mongo":
        # MongoDB 删除数据
        # 更新操作，修改匹配的 kdb_id 的 share 值
        result = db.share.update_one(
            {
                "share_type": "share",
                "information.kdb_id": kdb_id
            },
            {
                "$inc": {
                    "information.$.source": new_source  # 使用 $ 来定位匹配的元素
                }
            }
        )
        return result

    elif DB_DEFAULT == "sqlite":
        # SQLite 删除数据
        cursor = db.cursor()
        # 1. 从数据库中提取 information 字段
        cursor.execute("""
            SELECT information
            FROM share_kdb_info
            WHERE share_type = 'share';
        """)
        row = cursor.fetchone()

        # 2. 检查是否存在结果
        if row:
            information = json.loads(row[0])  # 解析 JSON 数据为 Python 字典列表
            
            # 3. 遍历列表，找到目标 kdb_id 并更新 source 值
            for item in information:
                if item.get("kdb_id") == kdb_id:
                    item["source"] = item.get("source", 0) + new_source  # 累加 source 值
                    break
            
            # 4. 将更新后的 JSON 数据写回数据库
            cursor.execute("""
                UPDATE share_kdb_info
                SET information = ?
                WHERE share_type = 'share';
            """, (json.dumps(information),))  # 转回 JSON 字符串
            db.commit()
            print("修改了共享文件的source")
            return True

        print("未找到匹配的共享文件")
        return False

def get_kdb_id():
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        # info = db.user.find({"information.kdb_id": kdb_id})
        result = db.share.find_one(
            {
                "share_type": "share",
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
        # SQLite 查询数据
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                json_extract(arr.value, '$.title') AS title,
                json_extract(arr.value, '$.kdb_id') AS kdb_id,
                json_extract(arr.value, '$.share') AS share
            FROM share_kdb_info, 
            json_each(share_kdb_info.information) AS arr
            WHERE share_kdb_info.share_type = ?;
        """, ("share",))

        db.commit()
        
        kdb_info = cursor.fetchall()
        # 直接将查询结果转换为字典格式
        titles = [{"title": row[0], "kdb_id": row[1], "share": row[2]} for row in kdb_info]
        return titles



def get_kdb_address(kdb_id):
    if DB_DEFAULT == "mongo":
        # MongoDB 查询数据
        # info = db.user.find({"information.kdb_id": kdb_id})
        result = db.share.find_one(
            {
                "share_type": "share",
            }
        )
        if result and "information" in result:
            info = result["information"]
            for i in info:
                if i["kdb_id"] == kdb_id:
                    return i["address"]
        else:
            print("No matching information found.")
            return False

    elif DB_DEFAULT == "sqlite":
        # SQLite 查询数据
        cursor = db.cursor()
        
        # 查询所有包含分享类型 'share' 的数据，并从 'information' 字段中提取包含 'kdb_id' 和 'address' 的 JSON 对象
        cursor.execute("""
            SELECT 
                json_extract(arr.value, '$.kdb_id') AS kdb_id,
                json_extract(arr.value, '$.address') AS address
            FROM share_kdb_info, 
            json_each(share_kdb_info.information) AS arr
            WHERE share_kdb_info.share_type = ?
        """, ("share",))

        db.commit()

        kdb_info = cursor.fetchall()
        
        # 查找指定的 kdb_id 的地址
        for row in kdb_info:
            if row[0] == kdb_id:  # row[0] 是 kdb_id，row[1] 是 address
                return row[1]  # 返回匹配的 address

        return False  # 如果没有找到对应的 kdb_id
