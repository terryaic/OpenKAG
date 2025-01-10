import pandas as pd
import os
from db import user_kdb_mgdb
import argparse

# 创建解析器
parser = argparse.ArgumentParser(description="分析Graphrag数据")

# 添加参数
parser.add_argument("--kdb_id", type=str, help="kdb_id")

# 解析命令行参数
args = parser.parse_args()

kdb_id = args.kdb_id
address = user_kdb_mgdb.get_address(kdb_id).get("address")
print("kdb的地址:",address)
GRAPHRAG_FOLDER=os.path.join(address, "db_files","output","latest","artifacts")

# 获取该文件夹内的所有文件
files_path = [
     os.path.join(GRAPHRAG_FOLDER, name) for name in os.listdir(GRAPHRAG_FOLDER)
    if os.path.isfile(os.path.join(GRAPHRAG_FOLDER, name)) and name.endswith(".parquet")
]

info = {}
for file_path in files_path:
    file_info = pd.read_parquet(file_path)
    # 获取 DataFrame 的行数
    num_rows = file_info.shape[0]
    info[os.path.splitext(os.path.basename(file_path))[0]] = num_rows

print("info:",info)