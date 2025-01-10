import os
from settings import SQL_DB_PATH_2USERS
import sqlite3
import shutil


current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQL_DB_PATH_2USERS)
db = sqlite3.connect(db_path, check_same_thread= False)

# 创建游标对象
cursor = db.cursor()

# SQL 查询以获取 email 列
query = "SELECT email FROM users"  # 替换为实际的表名
cursor.execute(query)

# 获取查询结果
email_list = cursor.fetchall()

# 输出结果
for email in email_list:
    print(email[0])  # 因为 fetchall 返回的是元组列表，每个元组是 (email,)

# 关闭连接
cursor.close()
db.close()


# 把default的文件拷贝到每一个用户的目录中
print("现在的地址：",current_directory)

# default setting的地址
def_set_yaml = os.path.join(current_directory, "stores", "default_setting","settings.yaml")
def_set_env = os.path.join(current_directory, "stores", "default_setting",".env")

print(f"配置文件的地址 {def_set_yaml} 和 {def_set_env}")

def user_set_path(user_id, kdb_id_list):
    print("用户名字：",user_id)
    if len(kdb_id_list) != 0:
        for kdb_id in kdb_id_list:
            path = []
            path.append(os.path.join(current_directory, "stores", "default", user_id, kdb_id, "db_files"))
        return path
    else:
        return False

def get_user_kdb(user_id):
    path = os.path.join(current_directory, "stores", "default", user_id)
    kdb_id_list = get_subdirectories(path)
    return kdb_id_list


def get_subdirectories(directory):
    """
    获取指定目录下的所有子目录的名字。

    :param directory: 目标目录路径
    :return: 子目录名字列表
    """
    if not os.path.exists(directory):
        print(f"路径 {directory} 不存在。")
        return []
    
    if not os.path.isdir(directory):
        print(f"路径 {directory} 不是一个目录。")
        return []

    # 列出目录内容并筛选子目录
    subdirectories = [
        name for name in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, name))
    ]
    return subdirectories


def copy_file_to_directory(src_file, dest_dir):
    """
    拷贝文件到指定目录，如果目录不存在则取消操作。
    如果目标目录中已存在同名文件，则覆盖该文件。

    :param src_file: 要拷贝的文件路径
    :param dest_dir: 目标目录路径
    :return: None
    """
    # 检查目标目录是否存在
    if not os.path.isdir(dest_dir):
        print(f"指定的目录 {dest_dir} 不存在，操作已取消。")
        return False

    # 检查源文件是否存在
    if not os.path.isfile(src_file):
        print(f"源文件 {src_file} 不存在。")
        return False

    # 目标文件路径
    dest_file = os.path.join(dest_dir, os.path.basename(src_file))

    # 拷贝文件，覆盖已存在的文件
    shutil.copy2(src_file, dest_file)
    print(f"文件已成功拷贝到 {dest_file}，若已存在则已覆盖。")
    return True


for email in email_list:
    kdb_id_list = get_user_kdb(email[0])
    print("kdb_id_list:",kdb_id_list)
    
    paths = user_set_path(email[0], kdb_id_list)

    if paths:
        for path in paths:
            #将文件拷贝到用户的目录下
            res = copy_file_to_directory(def_set_yaml, path)

            if res:
                print(f"用户{email} 拷贝成功")
            else:
                print(f"用户{email} 拷贝失败")

            res_env = copy_file_to_directory(def_set_env, path)
            if res:
                print(f"用户{email} 拷贝成功")
            else:
                print(f"用户{email} 拷贝失败")
    