import sqlite3
import json
import os
from pathlib import Path

working_directory = os.getcwd()

print("当前工作目录:", working_directory)


parent_dir = Path(working_directory).parents[2]

print(parent_dir)

json_file_path = os.path.join(working_directory, "info.json")

# 打开并加载 JSON 数据
with open(json_file_path, 'r') as f:
    json_data = json.load(f)

# 连接到 SQLite 数据库（如果没有会创建）
db_file_path = os.path.join(parent_dir, "data/chat.db")

conn = sqlite3.connect(db_file_path)
cursor = conn.cursor()

# 假设 JSON 数据包含字段 'id', 'name', 'age'，需要在 SQLite 创建一个表
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_kdb_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    information TEXT
);
''')

user_id = json_data["user_id"]
information = json_data["information"]
# 将 information 转换为 JSON 字符串
information_json = json.dumps(information)
# 插入 JSON 数据到数据库
print("数据：", user_id)

print("数据：", information_json)

cursor.execute('''INSERT INTO user_kdb_info (user_id, information) VALUES (?, ?)''', 
                (user_id, information_json))
print("传送成功")
# 提交事务并关闭连接
conn.commit()
conn.close()
