import json
import os
import time
import pymongo
import sqlite3
from settings import MONGODB_HOST, MONGODB_PORT, DB_DEFAULT, SQL_DB_PATH_2USERS,DBNAME
current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQL_DB_PATH_2USERS)


def get_user_role(user_id):
    # SQLite 查询数据
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    cursor.execute("SELECT role FROM users WHERE email = ?", (user_id,))
    row = cursor.fetchone()
    # 关闭连接
    cursor.close()
    db.close()
    return row[0] if row else None
