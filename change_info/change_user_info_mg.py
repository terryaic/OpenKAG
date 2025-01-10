import json
from pymongo import MongoClient
import os

# 获取当前工作目录
working_directory = os.getcwd()

print("当前工作目录:", working_directory)

# 连接到 MongoDB
client = MongoClient("localhost", 27017)
db = client["chatMongo"]

collection = db['user']  # 选择集合

file_path = os.path.join(working_directory, "info.json")

print("file_path", file_path)
print(os.path.isfile(file_path))
if os.path.isfile(file_path):
    print("存在文件")
    # 读取 JSON 文件
    with open(file_path, 'r') as file:
        data = json.load(file)  # 加载 JSON 数据

    # 插入数据到 MongoDB
    if isinstance(data, list):  # 如果数据是一个列表，批量插入
        collection.insert_many(data)
    else:  # 如果数据是一个字典，插入单个文档
        collection.insert_one(data)

    print("数据已成功插入 MongoDB!")
