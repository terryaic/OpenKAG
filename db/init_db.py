from settings import SQLITE_DB_PATH
import sqlite3
import os
import threading

current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQLITE_DB_PATH)

db_dir = os.path.dirname(db_path)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir)

db = sqlite3.connect(db_path, check_same_thread= False)
db.row_factory = sqlite3.Row

db_lock = threading.Lock()


def execute_sql(sql_query, params=None, fetchone=False):
    """
    执行动态 SQL 查询，并确保线程安全。
    
    :param sql_query: 要执行的 SQL 查询语句
    :param params: SQL 查询的参数（可选）
    :param fetchone: 是否返回一行数据。如果为 True，返回一行；否则返回所有结果。
    :return: 查询结果或插入数据的 ID。
    """
    if params is None:
        params = ()
    try:
        with db_lock:  # 使用锁来确保线程安全
            cursor = db.cursor()

            # 执行 SQL 语句
            cursor.execute(sql_query, params)

            # 如果是 SELECT 查询，返回相应的结果
            if sql_query.strip().upper().startswith(("SELECT", "PRAGMA")):
                if fetchone:
                    # 返回查询的第一行
                    return cursor.fetchone()
                else:
                    # 返回查询的所有结果
                    return cursor.fetchall()

            # 对于写操作（INSERT, UPDATE, DELETE），提交事务并返回插入的行 ID
            db.commit()
            return cursor.lastrowid
    
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        db.rollback()  # 如果有异常，回滚事务
        return None
