from datetime import datetime
from fastapi.responses import FileResponse
from fastapi import Request, HTTPException
import asyncio
from pathlib import Path
import uuid
from pydantic import BaseModel
# routers/graphrag.py
from fastapi import APIRouter
import os
from settings import DEFAULT_SETTINGS_PATH
from starlette.templating import Jinja2Templates
from fastapi import Request, UploadFile, File, Form, Body
import shutil
from fileprocesspipeline import FileProcessPipeline
from settings import ALLOWEDEXTENSIONS, MUlTIMODAL_ALLOWEDEXTENSIONS
from db import user_kdb_mgdb,file_db, user_kdb_info, share_info, doc_id_db,session_mgr,session_file_db,modb_api
from kdbmanager import kdbm
from fastapi.responses import FileResponse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import time
from apis.version1.route_login import get_resource
from fastapi.responses import StreamingResponse
from urllib.parse import quote
from .graphrag import get_user_path
import shutil
from auth.check_login import check_login
import json
from typing import List
from PIL import Image
import tempfile

# 请求体的数据模型
class FileDownloadRequest(BaseModel):
    kdb_id: str
    path_dir: list
    filename: str
    if_from_upload: bool

class SessionRequest(BaseModel):
    session_id: str
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()


@router.get("/showkdb", include_in_schema=False)
async def show_kdb(request: Request):
    response = await check_login(request)
    if response:
        return response
    user_id = request.cookies.get("current_user")
    user_path = os.path.join(get_user_path(), user_id)
    os.makedirs(user_path, exist_ok=True)
    return templates.TemplateResponse("graph/showkdb.html", {"request": request, "resources": get_resource(request, "showkdb")})

# 点击知识库触发
@router.post("/get_kdb")
async def get_kdb(request:Request):
    import json

    user_id = request.cookies.get("current_user")
    if not user_id:
        return None
    else:
        flag_user = user_kdb_info.get_user_exist(user_id)
        data = []
        print("用户是否已经存在user_kdb_info中:",flag_user)
        if not(flag_user is None):
            # 用户存在数据库中
            data = user_kdb_info.get_user_exist(user_id)
        else:
            # 不存在数据库中
            user_kdb_info.create_user_info(user_id)


        return {"user_info":data}


@router.post("/get_share_kdb")
async def get_share_kdb(request:Request):
    flag = share_info.get_share_exist()
    data = []
    print("是否已经存在share_info:",flag)
    if not(flag is None):
        # 用户存在数据库中
        data =share_info.get_share_exist()
        # if not data:
    else:
        # 不存在数据库中
        share_info.create_share_info()
    return {"share_info":data}


@router.post("/get_share_user_rag")
async def get_share_user_kdb(request:Request):
    import json

    all_kdb = {"user":[],"share":[]}

    user_id = request.cookies.get("current_user")

    if not user_id:
        return None

    else:
        kdb_id_user_list = user_kdb_info.get_kdb_id(user_id)
        def_path = get_user_path()

        kdb_id_user_file_list = []

        for info in kdb_id_user_list:
            kdb_id = info.get("kdb_id")
            res_directory = os.path.join(def_path, user_id, kdb_id, "res_files")

            # 判断文件夹内是否有文件
            if os.path.exists(res_directory) and os.path.isdir(res_directory):
                if len(os.listdir(res_directory)) > 0:
                   kdb_id_user_file_list.append(info)

        all_kdb["user"] = kdb_id_user_file_list

        kdb_id_share_list = share_info.get_kdb_id()

        kdb_id_share_file_list = []

        # 检查是否存在需要的文件
        for info in kdb_id_share_list:
            kdb_id = info.get("kdb_id")
            address_kdb = share_info.get_kdb_address(kdb_id)
            res_directory = os.path.join(address_kdb, "res_files")

             # 判断文件夹内是否有文件
            if os.path.exists(res_directory) and os.path.isdir(res_directory):
                if len(os.listdir(res_directory)) > 0:
                   kdb_id_share_file_list.append(info)

        all_kdb["share"] = kdb_id_share_file_list

        return all_kdb


@router.post("/get_share_user_graphrag")
async def get_share_user_kdb(request:Request):
    import json

    all_kdb = {"user":[],"share":[]}

    user_id = request.cookies.get("current_user")

    if not user_id:
        return None

    else:
        kdb_id_user_list = user_kdb_info.get_kdb_id(user_id)

        kdb_id_user_file_list = []

        parquet_list=[
            "create_final_nodes.parquet",
            "create_final_community_reports.parquet",
            "create_final_text_units.parquet",
            "create_final_relationships.parquet",
            "create_final_entities.parquet",
        ]

        # 检查是否存在需要的文件
        for info in kdb_id_user_list:
            kdb_id = info.get("kdb_id")
            graphrag_input_dir_path = os.path.join(get_user_path(), user_id, kdb_id, "db_files",
                               "output", "latest", "artifacts")

            # 检查每个文件是否存在
            all_files_exist = all(os.path.exists(graphrag_input_dir_path +  "/" +file) for file in parquet_list)

            if all_files_exist:
                kdb_id_user_file_list.append(info)


        all_kdb["user"] = kdb_id_user_file_list

        kdb_id_share_list = share_info.get_kdb_id()

        kdb_id_share_file_list = []

        # 检查是否存在需要的文件
        for info in kdb_id_share_list:
            kdb_id = info.get("kdb_id")
            address_kdb = share_info.get_kdb_address(kdb_id)
            graphrag_input_dir_path = os.path.join(address_kdb, "db_files",
                               "output", "latest", "artifacts")

            # 检查每个文件是否存在
            all_files_exist = all(os.path.exists(graphrag_input_dir_path +  "/" +file) for file in parquet_list)

            if all_files_exist:
                kdb_id_share_file_list.append(info)

        all_kdb["share"] = kdb_id_share_file_list

        return all_kdb


@router.get("/toCreateNewkdb", include_in_schema=False)
async def create_kdb(request: Request, kdb_id: str):
    response = await check_login(request)
    if response:
        return response
    resource = get_resource(request, "create_kdb")
    value = resource.get("new_kdb")
    return templates.TemplateResponse("graph/create_kdb.html", {"request": request, "kdb_id": kdb_id,
                                                                "value": value, "share": False, "is_from_share": False,
                                                                "permissions": get_permissions(request),
                                                                "resources": resource})


@router.get("/toKnowledgeBase", include_in_schema=False)
async def create_kdb(request: Request, kdb_id: str, title: str, share_type: bool, is_from_share: bool):
    return await check_login(request) or \
    templates.TemplateResponse("graph/create_kdb.html", {"request": request, "kdb_id": kdb_id,
                                                                "value": title, "share": share_type,
                                                                "is_from_share": is_from_share, "permissions": get_permissions(request),
                                                                "resources": get_resource(request, "create_kdb")})


@router.get("/backShowKdb", include_in_schema=False)
async def backShowKdb(request: Request):
    return await check_login(request) or \
    templates.TemplateResponse("graph/showkdb.html", {"request": request, "resources": get_resource(request, "showkdb")})


@router.post("/addNewkdb", include_in_schema=False)
async def addNewinfo(request: Request):
    import json

    try:
        body = await request.json()  # 获取请求体
        kdb_date = body.get('kdb_date')  # 提取 kdb_date

        user_id = request.cookies.get("current_user")

        #生成唯一的kdb_id
        kdb_id_uuid = uuid.uuid4().hex

        address = os.path.join(get_user_path(), user_id, kdb_id_uuid)

        resource = get_resource(request, "create_kdb")
        new_kdb_name = resource.get("new_kdb")

        user_kdb_info.add_user_kdb(address, kdb_id_uuid, new_kdb_name,
                                   kdb_date, 0, False, user_id, 0)

        user_kdb_mgdb.add_address_kdb(address, kdb_id_uuid)

         # 初始化 upload res db 文件夹
        UPLOAD_PATH = get_user_path()
        upload_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id_uuid, "uploaded_files")
        os.makedirs(upload_directory, exist_ok=True)

        db_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id_uuid, "db_files")
        os.makedirs(db_directory, exist_ok=True)
        # 把graphrag的初始文件法放入db_files中
        shutil.copytree(DEFAULT_SETTINGS_PATH, db_directory,dirs_exist_ok=True)

        res_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id_uuid, "res_files")
        os.makedirs(res_directory, exist_ok=True)

        return {"success": True, "kdb_id": kdb_id_uuid}

    except Exception as e:
        return {"error": f"未知错误: {str(e)}"}
    

@router.post("/txtCreateKdb")
async def txtCreateKdb(file: UploadFile):
    print("file:",file)
    print("开始处理文件")
    kdb_date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")  # 年月日-小时-分钟-秒

    user_id = "system_user"

    #生成唯一的kdb_id
    kdb_id = uuid.uuid4().hex

    address = os.path.join(get_user_path(), user_id, kdb_id)

    new_kdb_name = "系统测试的知识库"

    user_kdb_info.add_user_kdb(address, kdb_id, new_kdb_name,
                                kdb_date, 0, False, user_id, 0)

    user_kdb_mgdb.add_address_kdb(address, kdb_id)

    # 初始化 upload res db 文件夹
    UPLOAD_PATH = get_user_path()
    upload_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "uploaded_files")
    os.makedirs(upload_directory, exist_ok=True)

    db_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "db_files")
    os.makedirs(db_directory, exist_ok=True)
    # 把graphrag的初始文件法放入db_files中

    res_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "res_files")
    os.makedirs(res_directory, exist_ok=True)

    try:
        # 接收文件  
        file_name = file.filename
        file_path = os.path.join(upload_directory, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
        print("文件的地址是：",file_path)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    #添加到rag中做索引和emb
    kdb = await kdbm.create_or_get_rag(kdb_id=kdb_id)
    await kdb.add_document(file_path)

    return {"success": True, "kdb_id": kdb_id}


@router.post("/delete_kdb")
async def delete_kdb(request: Request):
    body = await request.json()  # 解析请求体
    kdb_id = body.get('kdb_id')  # 获取 old_title
    user_id = request.cookies.get("current_user")

    # 删除文件夹
    import shutil
    import os

    try:

        # 目标文件夹路径
        folder_path = os.path.join(get_user_path(), user_id, kdb_id)

        # 检查文件夹是否存在
        if os.path.exists(folder_path):
            # 使用 rmtree 递归删除文件夹及其所有内容
            shutil.rmtree(folder_path)
        else:
            print(f"文件夹不存在：{folder_path}")

        share_type = user_kdb_info.get_share_type(user_id, kdb_id)
        user_kdb_info.delete_kdb(user_id, kdb_id)

        if share_type:
            share_info.delete_kdb(kdb_id)

        user_kdb_mgdb.delete_kdb(kdb_id)

        doc_id_db.delete_user_kdb_doc(kdb_id)

        return {"is_delete": True}

    except Exception as e:
        return {"error": f"未知错误: {str(e)}"}


@router.post("/delete_muilt_kdb")
async def delete_muilt_kdb(request: Request):
    body = await request.json()  # 解析请求体
    kdb_id_list = body.get('kdb_id_list')  # 获取 old_title
    print("批量删除的kdb",kdb_id_list)
    user_id = request.cookies.get("current_user")
    try:
        for kdb_id in kdb_id_list:
            # 目标文件夹路径
            folder_path = os.path.join(get_user_path(), user_id, kdb_id)

            # 检查文件夹是否存在
            if os.path.exists(folder_path):
                # 使用 rmtree 递归删除文件夹及其所有内容
                shutil.rmtree(folder_path)
            else:
                print(f"文件夹不存在：{folder_path}")

        user_kdb_info.delete_muilt_kdb(user_id, kdb_id_list)

        share_info.delete_muilt_kdb(kdb_id_list)

        user_kdb_mgdb.delete_muilt_kdb(kdb_id_list)

        doc_id_db.delete_muilt_user_kdb_doc(kdb_id_list)

        return {"is_delete": True}

    except Exception as e:
        return {"error": f"未知错误: {str(e)}"}


@router.post("/change_kdb_title")
async def change_kdb_title(request: Request):
    body = await request.json()  # 解析请求体
    kdb_id = body.get('kdb_id')  # 获取 old_title
    new_title = body.get('new_title')  # 获取 new_title
    user_id = request.cookies.get("current_user")

    if not user_id:
        return {"is_change": False}
    else:
        share_type = user_kdb_info.get_share_type(user_id, kdb_id)
        user_kdb_info.change_kdb_title(user_id, kdb_id, new_title)
        if share_type:
            # 如果是分享的就修改分享的title
            share_info.change_kdb_title(kdb_id, new_title)

        return {"is_change": True}


@router.post("/change_kdb_share")
async def change_kdb_share(request: Request):
    body = await request.json()  # 解析请求体
    kdb_id = body.get('kdb_id')  # 获取 old_title
    share_type = body.get('share_type')  # 获取 new_title
    user_id = request.cookies.get("current_user")

    if not user_id:
        return {"is_change": False}
    else:
        user_kdb_info.change_kdb_share(user_id, kdb_id, share_type)
        info = user_kdb_info.get_user_kdb(user_id, kdb_id)
        if share_type:
            share_info.add_kdb(info)
        else:
            # 删除share中的信息
            share_info.delete_kdb(kdb_id)

        return {"is_change": True}

def change_source(user_id, kdb_id, len_file, doc_len):
    share_type = user_kdb_info.get_share_type(user_id, kdb_id)

    if len_file >= 0:
        user_kdb_info.change_kdb_doc(user_id, kdb_id, doc_len)
    #修改kdb的source的值
    mes = user_kdb_info.change_kdb_source(user_id, kdb_id, len_file)

    if share_type:
        share_info.change_kdb_source(kdb_id, len_file)


    return {"is_finish": True}


progress_info = {}

def get_permissions(request: Request):
    from apis.version1.route_login import get_user_role
    from settings import USER_PERMISSIONS
    role = get_user_role(request=request)
    permissions = USER_PERMISSIONS[role]
    return permissions

@router.post("/upload_files")
async def upload_files(request: Request, kdb_id: str = Form(...), files: list[UploadFile] = File(...)):
    try:
        print(f"开始上传文件到知识库: {kdb_id}, 文件数量: {len(files)}")

        user_id = request.cookies.get("current_user")
        resource = get_resource(request, "create_kdb")

        # 初始化上传路径
        UPLOAD_PATH = get_user_path()
        upload_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "uploaded_files")
        os.makedirs(upload_directory, exist_ok=True)
        rep_len = 0
        current_time = datetime.now()
        file_names = []
        for file in files:
            file_path = os.path.join(upload_directory, file.filename)
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            if os.path.exists(file_path):
                print(f"文件 {file.filename} 已存在, 覆盖")
                await file_db.update_create_time(kdb_id, file_path, formatted_time)
                doc_id_db.delete_doc_id(kdb_id, file.filename)
                rep_len +=1
            else:
                #保存文件的信息
                await file_db.insert_file_info(kdb_id, False, formatted_time, file_path)


            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # 验证文件是否保存成功
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                raise FileNotFoundError(f"文件保存失败: {file.filename}")
            else:
                # 记录保存的文件
                file_names.append(file.filename)

        file_len = len(file_names)

        # 保存文件数量到数据库中
        print(f"成功保存的文件:",file_names)
        print(f"成功保存的文件: {file_len}")
        save_len = file_len - rep_len
        change_source(user_id, kdb_id, save_len, file_len)

        if rep_len:
            return {"no_upload": False, "message": f"{resource.get('suc_upload')} {file_len} \
                    {resource.get('get_file')} {resource.get('have')} {rep_len} {resource.get('duplicate_file')}","file_names":file_names}

        return {"no_upload": False, "message": f"{resource.get('suc_upload')} {file_len} {resource.get('get_file')}","file_names":file_names}

    except Exception as e:
        print(f"文件上传失败: {str(e)}")
        return {"no_upload": True, "message": f"{resource.get('upload_fail')}!"}


def get_current_language(request):
    current_language = request.cookies.get("current_language")
    # 通过current_language获得语言
    if not current_language:
        # 从请求头中提取 'Accept-Language'
        current_language = request.headers.get("accept-language")
        if current_language:
            # 解析 'Accept-Language' 获取首选语言
            current_language = [lang.split(";")[0].strip() for lang in current_language.split(",")][0]
    return current_language


def an_delete_file(res_directory, uploaded_file_path):
    if os.path.exists(uploaded_file_path):
        os.remove(uploaded_file_path)  # 删除文件

    file_path_without_ext = os.path.splitext(uploaded_file_path)[0]
    if os.path.exists(file_path_without_ext):
        os.rmdir(file_path_without_ext)  # 删除文件

    # 同时去除res文件夹的文件
    filename_with_extension = os.path.basename(uploaded_file_path)
    file_name = os.path.splitext(filename_with_extension)[0] + ".txt"
    res_file_path = os.path.join(res_directory, file_name)
    print("文件发生错误",res_file_path)
    if os.path.exists(res_file_path):
        os.remove(res_file_path)  # 只有在文件存在时才删除


class UserAnalyzeTask:
    def __init__(self, user_id, file_names):
        """
        初始化用户任务
        :param user_id: 用户 ID
        :param file_names: 已保存的文件列表
        """
        self.user_id = user_id  # 用户 ID
        self.saved_files = file_names  # 已保存文件列表
        self.fail_files = []  # 失败文件列表
        self.is_finish = False  # 是否完成标志
        self.is_error = False  # 是否出错标志
        self.now_progress = []  # 当前进度
        self.un_analyze_file = []  # 未分析文件列表

    def to_dict(self):
        """
        将对象转换为字典形式
        :return: 字典形式的用户任务
        """
        return {
            "user_id": self.user_id,
            "saved_files": self.saved_files,
            "fail_files": self.fail_files,
            "is_finish": self.is_finish,
            "is_error": self.is_error,
            "now_progress": self.now_progress,
            "un_analyze_file": self.un_analyze_file,
        }

    def __repr__(self):
        """
        返回对象的字符串表示
        :return: 字符串
        """
        return str(self.to_dict())
    
@router.post("/analyze_files")
async def analyze_files(request: Request, data:dict):
    start_time = time.time()

    kdb_id = data.get("kdb_id")
    prompt_name = data.get("prompt_name")
    if_use_muilt = data.get("if_use_muilt")
    file_names = data.get("file_names")

    if not file_names:
        return {"is_an":False,"message": "没有找到需要分析的文件"}

    user_id = request.cookies.get("current_user")

    UPLOAD_PATH = get_user_path()

    upload_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "uploaded_files")

    uploaded_files = [ os.path.join(upload_directory, file_nmae) for file_nmae in file_names]

    print("文件的地址：",uploaded_files)

    resource = get_resource(request, "create_kdb")

    print(f"开始分析文件, prompt_name: {prompt_name}, kdb_id: {kdb_id}, if_use_muilt: {if_use_muilt} 上传的文件有: {file_names}")

    current_language = get_current_language(request)
    print("上传文件获得到的最终的语言是：",current_language)

    # 初始化路径
    res_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "res_files")
    os.makedirs(res_directory, exist_ok=True)

    # 初始化任务
    pipeline = FileProcessPipeline(res_directory)
    kdb = await kdbm.create_or_get_rag(kdb_id=kdb_id)

    num_doc = user_kdb_info.get_kdb_doc(kdb_id)
    print("当前的doc是:",num_doc)

    user_task = {"user_id":user_id,"saved_files":file_names, "fail_files":[],
                  "is_finish":False, "is_error":False, "now_progress":[],"un_analyze_file":[]}
    
    progress_info[kdb_id] = user_task
    print("上传任务：", progress_info)

    len_file = 0

    delete_len = 0

    support_multi_modal = True if 'multimodal' in get_permissions(request) else False
    print("是否支持多模态：",support_multi_modal)

    # try:
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor() as executor:
        tasks = []

        for file_path in uploaded_files:
            file_name = os.path.basename(file_path)
            print("文件的地址",file_path)
            len_file += 1

            # 验证文件是否保存成功
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                raise FileNotFoundError(f"{resource.get('fail_save_mes')}: {file_path}")

            # 定义文件处理函数
            def process_file_wrapper(pipeline, file_path, support_multi_modal, if_use_muilt, doc_id, prompt_name, user_id, kdb_id, filename, user_task):
                try:
                    # 检查是否已经有保存图片的文件
                    # 使用 Path 对象获取目录，并去掉文件扩展名
                    directory_without_extension = Path(file_path).parent / Path(file_path).stem

                    # 检查文件夹是否存在
                    if os.path.exists(directory_without_extension) and os.path.isdir(directory_without_extension):
                        # 删除文件夹及其内容
                        shutil.rmtree(directory_without_extension)
                        print(f"文件夹 {directory_without_extension} 已删除")

                    name, extension = os.path.splitext(filename)
                    if extension == ".doc" or extension == ".ppt":
                        # 删除pdf文件
                        pdf_file_name = name + ".pdf"
                        file_path_doc_ppt = os.path.join(os.path.dirname(file_path),pdf_file_name)
                        if os.path.exists(file_path_doc_ppt):
                            print("删除doc或者ppt的pdf的文件",file_path_doc_ppt)
                            os.remove(file_path_doc_ppt)

                    outfile = pipeline.process_file(file_path, doc_id, prompt_name, current_language, support_multi_modal and if_use_muilt, extract_text=False)

                    # 更新进度
                    user_task.get("now_progress").append(filename)

                    # 如果处理失败，删除文件并记录失败文件
                    if outfile is None:
                        user_task.get("un_analyze_file").append(os.path.basename(file_path))
                    else:
                        doc_id_db.add_doc_id(user_id, kdb_id, doc_id, filename, None)
                    return outfile

                except Exception as e:
                    # 如果发生任何异常，记录文件并抛出异常
                    user_task["is_error"] = True
                    user_task.get("fail_files").append(os.path.basename(file_path))
                    print(f"处理文件 {file_path} 时发生错误: {e}")
                    return e  # 返回异常对象

            # 分配文档 ID
            doc_id = num_doc - len(uploaded_files) + len_file

            # 提交任务到线程池
            task = loop.run_in_executor(executor, process_file_wrapper, pipeline, file_path, support_multi_modal, if_use_muilt, doc_id, prompt_name, user_id, kdb_id, file_name, user_task)
            tasks.append(task)


        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for file_path, result in zip(uploaded_files, results):
            print("分析的结果：", result)
            if isinstance(result, Exception):
                # 删除已保存的文件，处理异常
                if os.path.exists(file_path):
                    delete_len -= 1
                    an_delete_file(res_directory, file_path)
            else:
                # 确保结果为有效路径
                if result is None:
                    delete_len -= 1  # 文件处理失败时，减少 len_file 的值
                    an_delete_file(res_directory, file_path)
                else:
                    await kdb.add_document(file_path=result)

        change_source(user_id, kdb_id, delete_len, 0)
        user_task["is_finish"] = True

        finish_time = time.time() - start_time

        print(f"用户 {user_id} 的 {kdb_id} 的kdb 分析 {len(file_names) - delete_len} 个文件使用了 {finish_time} s")


def get_files_and_folders(directory_path, is_rel= False):
        folders_dict = {}  # 存储目录及其对应的文件列表

        # 获取传入目录的绝对路径
        base_path = os.path.abspath(directory_path)

        # 遍历当前目录的内容
        for entry in os.listdir(directory_path):
            entry_path = os.path.join(directory_path, entry)
            relative_path = os.path.relpath(entry_path, base_path)  # 计算相对路径

            if os.path.isfile(entry_path):
                # 如果是文件，添加到当前目录的文件列表
                folder_name = os.path.dirname(relative_path)  # 获取该文件的父级目录

                # 如果文件在根目录下（例如 'data' 目录），就归类到 'data'
                if folder_name == '':  # 直接在传入目录下的文件
                    folder_name = os.path.basename(directory_path)  # 归入根目录名（如 'data'）

                # 构建父目录路径，确保文件被归类到 `data/data_1` 等正确的目录
                if folder_name not in folders_dict:
                    folders_dict[folder_name] = []

                if not is_rel:
                    folders_dict[folder_name].append(os.path.abspath(entry_path))  # 将文件的绝对路径加入该目录列表
                else:
                    folders_dict[folder_name].append(entry)  # 将文件的绝对路径加入该目录列表

            elif os.path.isdir(entry_path):
                # 如果是文件夹，递归处理子目录
                sub_folders_dict = get_files_and_folders(entry_path)  # 获取子文件夹及文件
                # 将子目录和子文件的结果加入到当前目录字典
                for folder, files in sub_folders_dict.items():
                    # 在子目录前加上父目录的名字来保持层级结构
                    full_folder_name = os.path.join(os.path.basename(directory_path), folder)
                    if full_folder_name not in folders_dict:
                        folders_dict[full_folder_name] = []
                    folders_dict[full_folder_name].extend(files)

        return folders_dict


@router.post("/analyze_files_ad")
async def analyze_files_ad(request: Request):
    start_time = time.time()
    body = await request.json()  # 解析请求体
    kdb_id = body.get('kdb_id')  
    if_use_muilt = body.get('if_use_muilt') 
    address = body.get('address')
    # 从查询参数中获取数据
    print("kdb_id是",kdb_id)
    print("文件夹的地址是",address)
    print("是否使用多模态",if_use_muilt)

    folders_dict = get_files_and_folders(address)
    print("文件夹：",folders_dict) 
    
    data_dir = list(folders_dict.keys())
    print("文件夹的地址：",data_dir) 
    # 在upload和res生成对应的目录

    def create_folders(base_dir, subfolder_list):
        file_paths = []
        for subfolder in subfolder_list:
            # 拼接base_dir和子文件夹的相对路径，形成完整路径
            folder_path = os.path.join(base_dir, subfolder)
            file_paths.append(folder_path)
            # 创建文件夹，包括父文件夹（如果它们不存在）
            os.makedirs(folder_path, exist_ok=True)
            # print(f"创建文件夹: {folder_path}")
        
        return file_paths

    user_id = request.cookies.get("current_user")

    default_path = get_user_path()

    current_language = get_current_language(request)

    print("上传文件获得到的最终的语言是：",current_language)

    # 初始化任务
    kdb = await kdbm.create_or_get_rag(kdb_id=kdb_id)
    print("初始化kdd mag",kdb)

    # 初始化路径
    res_directory = os.path.join(default_path, user_id, kdb_id, "res_files")
    os.makedirs(res_directory, exist_ok=True)

    uploaded_directory = os.path.join(default_path, user_id, kdb_id, "uploaded_files")
    os.makedirs(uploaded_directory, exist_ok=True)

    create_folders(res_directory, data_dir)
    create_folders(uploaded_directory, data_dir)

    num_doc = user_kdb_info.get_kdb_doc(kdb_id)

    len_file = 0

    delete_len = 0

    support_multi_modal = True if 'multimodal' in get_permissions(request) else False
    print("是否支持多模态：",support_multi_modal)

    # 定义文件处理函数
    def process_file_wrapper(pipeline, file_path, support_multi_modal, if_use_muilt, doc_id, prompt_name, user_id, kdb_id, filename, dir):
        try:
            # 使用 Path 对象获取目录，并去掉文件扩展名
            directory_without_extension = Path(file_path).parent / Path(file_path).stem
            print("删除文件夹：",directory_without_extension)
            # 检查文件夹是否存在
            if os.path.exists(directory_without_extension) and os.path.isdir(directory_without_extension):
                # 删除文件夹及其内容
                shutil.rmtree(directory_without_extension)

            name, extension = os.path.splitext(filename)
            if extension == ".doc" or extension == ".ppt":
                # 删除pdf文件
                pdf_file_name = name + ".pdf"
                file_path_doc_ppt = os.path.join(os.path.dirname(file_path),pdf_file_name)
                if os.path.exists(file_path_doc_ppt):
                    print("删除doc或者ppt的pdf的文件",file_path_doc_ppt)
                    os.remove(file_path_doc_ppt)

            outfile = pipeline.process_file(file_path, doc_id, prompt_name, current_language, support_multi_modal and if_use_muilt, extract_text=False)
            print("分析文件的结果:",outfile)
            # 如果是空则删除upload上的文件
            if not outfile:
                pass
            else:
                doc_id_db.add_doc_id(user_id, kdb_id, doc_id, dir + "/"+ filename, None)
            return outfile
        
        except Exception as e:
            # 如果发生任何异常，记录文件并抛出异常
            print(f"处理文件 {file_path} 时发生错误: {e}")
            return e  # 返回异常对象

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor() as executor:
        tasks = []

        for dir in data_dir:
            # print("初始化pipleline:",key)
            files = folders_dict.get(dir)
            res_p = os.path.join(res_directory, dir)
            up_p = os.path.join(uploaded_directory, dir)
            pipeline = FileProcessPipeline(res_p, up_p)
            for file_path in files:
                file_name = os.path.basename(file_path)
                len_file += 1

                # 分配文档 ID
                doc_id = num_doc + len_file

                # 提交任务到线程池
                task = loop.run_in_executor(executor, process_file_wrapper, pipeline, file_path, support_multi_modal, if_use_muilt, doc_id, "", user_id, kdb_id, file_name, dir)
                tasks.append(task)


        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            print("结果是：",result)
            if isinstance(result, Exception):
                print("发生了错误")
                pass
            else:
                if result is None:
                    delete_len += 1 
                else:
                    await kdb.add_document(file_path=result)

        end_time = time.time() - start_time
        print("######################################")
        print(f"user: {user_id} 的 kdb: {kdb_id} 分析了 {len_file} 个文件, 有 {delete_len} 个文件发生了错误 花费了 {end_time}")
        print("######################################")

        return {"success": True, "message": f"user: {user_id} 的 kdb: {kdb_id} 分析了 {len_file} 个文件, 有 {delete_len} 个文件发生了错误 花费了 {end_time}"}


@router.post("/files")
async def files(request: Request, kdb_id_data: dict):
    kdb_id = kdb_id_data.get("kdb_id")  # 从字典中提取 kdb_id
    address = user_kdb_mgdb.get_address(kdb_id)["address"]
    upload_directory = os.path.join(address, "uploaded_files")

    if not os.path.isdir(upload_directory):
        return []
    doc_ppt_file_list = []
    files = []
    for filename in os.listdir(upload_directory):
        
        name, extension = os.path.splitext(filename)
        if extension == ".doc" or extension == ".ppt":
            doc_ppt_file_list.append(name+".pdf")

        file_path = os.path.join(upload_directory, filename)
        # 检查是否为文件
        if os.path.isfile(file_path):
            # 过滤掉临时文件和锁定文件
            if filename.endswith('.tmp') or filename.startswith(('_lock.', '.~')):
                continue  # 跳过临时文件
            files.append(filename)

    files= [filename for filename in files if filename not in doc_ppt_file_list]

    return files


@router.post("/res_files")
async def res_files(request: Request, data: dict):
    kdb_id = data.get("kdb_id")  # 从字典中提取 kdb_id
    path_dir = data.get("path_dir")  # 从字典中提取 kdb_id
    address = user_kdb_mgdb.get_address(kdb_id)["address"]
    res_directory = os.path.join(address, "res_files", *path_dir)
    if not os.path.isdir(res_directory):
        print("这不是一个文件")
        return []
    file_dict = get_files_and_folders(res_directory,True)
    rep_dir = "res_files" if not path_dir else path_dir[-1]
    file_dict = {key.replace(f'{rep_dir}', '', 1).replace(f'/', '', 1): value for key, value in file_dict.items()}
    print("file_dict:",file_dict)
    return file_dict


@router.post("/showResFile")
async def showResFile(request: Request):
    body = await request.json()  # 解析请求体
    kdb_id = body.get('kdb_id')  # 获取 old_title
    path_dir = body.get("path_dir")  # 从字典中提取 kdb_id
    filename = body.get("filename")

    address = user_kdb_mgdb.get_address(kdb_id)["address"]
    file_path = os.path.join(address, "res_files", *path_dir, filename)
    print("file_path:",file_path)

    result = []
    with open(file_path, mode="r", encoding="utf-8") as file:
        for i, line in enumerate(file):
            if i >= 1000:  # 只读取前 1000 行
                break
            result.append(line)

    content = ''.join(result)  # 将结果合并为字符串
    return content

@router.delete("/files/{kdb_id}/{file_name}")
async def delete_file(request: Request, kdb_id: str, file_name: str):
    try:
        user_id = request.cookies.get("current_user")
        resource = get_resource(request, "create_kdb")

        # 初始化 upload res db 文件夹
        UPLOAD_PATH = get_user_path()
        upload_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "uploaded_files")
        res_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "res_files")
        name, extension = os.path.splitext(file_name)
        if extension == ".doc" or extension == ".ppt":
            pdf_file = name + ".pdf"
            pdf_path = os.path.join(upload_directory, pdf_file)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        res_file_name = name + ".txt"
        file_path = os.path.join(upload_directory, file_name)
        file_dir = os.path.join(upload_directory, name)
        res_file_path = os.path.join(res_directory, res_file_name)
        if os.path.exists(res_file_path):
            os.remove(res_file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            await file_db.delete_file(file_path)
            doc_id_db.delete_doc_id(kdb_id, file_name)
            change_source(user_id, kdb_id, -1, -1)
        if os.path.isdir(file_dir):
            shutil.rmtree(file_dir)

        if len(os.listdir(res_directory)) == 0:
            # 删除storge文件夹 和close rag
            storage_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "storage")
            shutil.rmtree(storage_directory)
            kdbm.release_rag(kdb_id=kdb_id)
            del kdbm.kdb_pool[kdb_id]
            rag_search = False 
        else:
            rag_search = True 

        return {"rag_search": rag_search, "message": f"{resource.get('file')}： '{file_name}' {resource.get('have_been_remove_mes')}！"}

    except Exception as e:
        return {"message": f"{resource.get('error')}: {str(e)}"}


@router.post("/build")
async def build(request: Request, kdb_id_data: dict):
    user_id = request.cookies.get("current_user")
    kdb_id = kdb_id_data.get("kdb_id")  # 从字典中提取 kdb_id

    resource = get_resource(request, "create_kdb")

    # 初始化 upload res db 文件夹
    def_path = get_user_path()

    res_directory = os.path.join(def_path, user_id, kdb_id, "res_files")

    # 判断文件夹内是否有文件
    if os.path.exists(res_directory) and os.path.isdir(res_directory):
        if len(os.listdir(res_directory)) > 0:
            kdb = await kdbm.create_or_get_rag(kdb_id=kdb_id)

            await kdb.build_knowledge_base(res_directory)

            return {"build": True, "message": f"{resource.get('successful_rebuild_rag')}!"}

        return {"build": False, "message": f"{resource.get('fail_rag_mes')}！"}



@router.post("/get_kdb_title")
async def get_kdb_title(request: Request, kdb_id: dict):
    try:
        kdb_id = kdb_id.get("kdb_id")
        resource = get_resource(request, "create_kdb")
        if not kdb_id:
            return {"title": None}

        title = user_kdb_info.get_kdb_title(kdb_id)

        return {"title": title}

    except Exception as e:
        return {"error": f"{resource.get('error')}: {str(e)}"}


@router.post("/download")
async def download(request: Request, file_request: FileDownloadRequest):
    filename = file_request.filename
    kdb_id = file_request.kdb_id
    path_dir = file_request.path_dir
    if_from_upload = file_request.if_from_upload
    user_dir_path = user_kdb_mgdb.get_address(kdb_id)["address"]
    if if_from_upload:
        file_path = os.path.join(user_dir_path, "uploaded_files", filename)
    else:
        file_path = os.path.join(user_dir_path, "res_files", *path_dir ,filename)
    print("下载文件的地址:",file_path)
    if os.path.exists(file_path):
        # 对文件名进行 UTF-8 编码以支持多语言字符
        encoded_filename = quote(filename)

        # 文件总大小
        file_size = os.path.getsize(file_path)

        # 使用分块方式读取文件
        def file_iterator():
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(1024 * 1024)  # 每次读取 1MB
                    if not chunk:
                        break
                    yield chunk

        # 返回 StreamingResponse 分块传输文件
        return StreamingResponse(
            file_iterator(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Length": str(file_size),  # 这会使浏览器显示下载进度
            },
        )
    else:
        return {"error": "File not found"}


@router.get("/get_image")
async def get_image(image_name: str, doc_id: str, kdb_id: str, session_id: str, resize: bool):
    if_kdb = None
    print("获得图片的kdb_id是",kdb_id)
    if kdb_id and kdb_id != "null":
        if_kdb = True
        file_path, user_id = doc_id_db.get_file_name(if_kdb, kdb_id, int(doc_id))
    else:
        if_kdb = False
        file_path, user_id = doc_id_db.get_file_name(if_kdb, session_id, int(doc_id))

    default_path=get_user_path()
    from urllib.parse import unquote
    image_name = unquote(image_name)
    if not file_path:
        return
    if not image_name.endswith(file_path):
        file_path, _ = os.path.splitext(file_path)

        # 拼接文件的完整路径
        if if_kdb:
            image_path = os.path.join(str(default_path), str(user_id), str(kdb_id), "uploaded_files", str(file_path), str(image_name))
        else:
            default_path = os.path.dirname(default_path)
            print("来自上传的根目录是",default_path)

            image_path = os.path.join(str(default_path), "session", str(user_id), str(session_id), "uploaded_files", str(file_path), str(image_name))
    else:
        if if_kdb:
            image_path = os.path.join(str(default_path),str(user_id), str(kdb_id), "uploaded_files", str(file_path))
        else:
            default_path = os.path.dirname(default_path)

            print("来自上传的根目录是",default_path)
            image_path = os.path.join(str(default_path), "session", str(user_id), str(session_id), "uploaded_files", str(file_path))
        

    print("图片的地址是 :",image_path)

    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    if not resize:
        # 返回图片文件
        return FileResponse(image_path)
    else:
        # 定义目标宽度和高度
        fixed_width = 300
        fixed_height = 300

        # 打开图片并调整大小
        img = Image.open(image_path)

        original_width, original_height = img.size

        # 判断图片方向
        if original_width > original_height:  # 横向图片
            scale_factor = fixed_width / original_width
            new_width = fixed_width
            new_height = int(original_height * scale_factor)
        else:  # 纵向图片或正方形图片
            scale_factor = fixed_height / original_height
            new_height = fixed_height
            new_width = int(original_width * scale_factor)

        # 调整图片大小
        resized_img = img.resize((new_width, new_height))

        print(f"图片 {image_path} 修改后的大小是 宽度是 {new_width} 高度是 {new_height}")
        # 保存调整后的图片到临时文件
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            resized_img.save(tmp.name, format="JPEG")
            return FileResponse(tmp.name)


@router.post("/check_el_pr_res_up")
async def check_el_pr_res_up(request: Request):
    """
    return {
            "show_graph":, "build_graph":,
            "rag_search":, "graphrag_search":,
            "is_uploading":
            }
    """
    body = await request.json()  # 获取请求体
    kdb_id = body.get('kdb_id')  # 提取 kdb_date
    is_from_share = body.get('is_from_share')  # 提取 kdb_date

    is_from_share = True if is_from_share == "True" else False

    address_kdb = user_kdb_mgdb.get_address(kdb_id).get("address")

    # 检查是否可以展示图谱
    el_file_path = os.path.join(address_kdb, "db_files", "output", "latest", "artifacts")

    entity_path = os.path.join(el_file_path, "create_final_entities.parquet")
    relationship_path = os.path.join(el_file_path, "create_final_relationships.parquet")

    if os.path.isfile(entity_path) and os.path.isfile(relationship_path):
        show_graph = True
    else:
        show_graph = False


    # 检查是否是第一次建立图谱
    graphrag_output_path = os.path.join(address_kdb, "db_files", "output")

    if os.path.isdir(graphrag_output_path):
        build_graph = True
    else:
        build_graph = False


    # 检查是否rag有文件
    rag_storage_directory = Path(os.path.join(address_kdb, "storage", "docstore.json"))
    if rag_storage_directory.exists():
        # with rag_storage_directory.open('r', encoding='utf-8') as file:
        #     try:
        #         content = json.load(file)  # 解析 JSON 文件
        #         rag_source = True if content else False
        #     except json.JSONDecodeError:
        #         print("Error: The file content is not valid JSON.")
        #         rag_source = False

        file_size = rag_storage_directory.stat().st_size  # 获取文件大小
        if file_size > 10:
            rag_source = True
        else:
            rag_source = False
    else:
        rag_source = False
    
    rag_res_directory = os.path.join(address_kdb, "res_files")
    if os.path.exists(rag_res_directory) and os.path.isdir(rag_res_directory):
        if len(os.listdir(rag_res_directory)) > 0:
            rag_res = True
        else:
            rag_res = False
    else:
        rag_res = False

    rag_search = True if rag_source and rag_res else False
    
    # 检查是否graphrag有文件
    parquet_list=[
                    "create_final_nodes.parquet",
                    "create_final_community_reports.parquet",
                    "create_final_text_units.parquet",
                    "create_final_relationships.parquet",
                    "create_final_entities.parquet",
                ]
    graphrag_input_dir_path = os.path.join(address_kdb, "db_files",
                                            "output", "latest", "artifacts")

    if os.path.exists(graphrag_input_dir_path) and os.path.isdir(graphrag_input_dir_path):
        all_files_exist = all(os.path.exists(graphrag_input_dir_path +  "/" +file) for file in parquet_list)
        if all_files_exist:
            graphrag_search = True
        else:
            graphrag_search = False
    else:
        graphrag_search = False

    if not is_from_share:
        # 检查是否有上传任务
        if kdb_id in progress_info:
            is_uploading = True
            print(f"用户: {progress_info.get(kdb_id)} 的 kdb: {kdb_id} 正在上传文件")
        else:
            is_uploading = False
    else:
        is_uploading = False

    all_info = {"show_graph":show_graph, "build_graph":build_graph,
            "rag_search":rag_search, "graphrag_search":graphrag_search,
            "is_uploading":is_uploading}

    print("all_info",all_info)
    return all_info


@router.post("/upload_check")
async def upload_check(request: Request):
    body = await request.json()  # 获取请求体
    kdb_id = body.get('kdb_id')  # 提取 kdb_date
    resource = get_resource(request, "create_kdb")

    # 检查是否有上传任务
    if kdb_id not in progress_info:
        return {"no_task": True, "saved_files":[]}

    # 有任务，判断是上传完成还是在正上传还是上传失败
    info = progress_info.get(kdb_id)

    """
        user_task = {"user_id":user_id,"saved_files":file_names, "fail_files":[],
                  "is_finish":False, "is_error":False, "now_progress":[],"un_analyze_file":[]}
    """
    if not info.get("is_finish"):
        print(f"用户: {info.get('user_id')} 的 kdb: {kdb_id} 正在分析文件 共有 {len(info.get('saved_files'))} 个文件 已经分析了 {len(info.get('now_progress'))} 个文件")
        saved_files = info.get("saved_files")
        finish_files = info.get("now_progress")
        is_emb = False
        mes = ""
        if set(saved_files).issubset(set(finish_files)):
            print("=========================")
            print(set(saved_files))
            print(set(finish_files))
            print("分析完成正在建立索引")
            is_emb = True
            mes = resource["is_emb"]
        return {"no_task": False,"saved_files":saved_files,"finish_file":finish_files,"is_emb":is_emb,"message":mes}
    else:
        print("info：",info)
        fail_files = info.get("fail_files")
        un_analyze_files = info.get("un_analyze_file")

        mes = ""

        if len(fail_files) != 0:
            print("分析文件发生错误")
            mes_error = resource.get('file') + " "
            for i in fail_files:
                mes_error += (i + " ")
            mes_error += (resource.get('file_error') or "" + " ")
            print("错误信息：",mes_error)
            mes += mes_error

        if len(un_analyze_files) != 0:
            print("分析文件发生错误")
            mes_fail = resource.get('file') + " "
            for i in un_analyze_files:
                mes_fail += (i + " ")
            mes_fail += (resource.get('file_error') or "" + " ")
            print("错误信息：",mes_fail)
            mes += mes_fail


        # 删除记录
        if kdb_id in progress_info:
            del progress_info[kdb_id]
            print(f"已清除进度信息: {kdb_id}")

        if mes:
            mes += resource.get('remove_file') + "!"
            print(mes)
            return {"no_task": True, "mesaage":mes}

        suf_mes = f"{resource.get('successful_analysis')} {len(info.get('saved_files'))} {resource.get('get_file')} !"
        print(suf_mes)
        return {"no_task": True, "mesaage":suf_mes}


@router.post("/graphrag_search_check")
async def graphrag_search_check(request: Request):
    body = await request.json()  # 获取请求体
    kdb_id = body.get('kdb_id')  # 提取 kdb_date

    address_kdb = user_kdb_mgdb.get_address(kdb_id).get("address")

    # 检查是否graphrag有文件
    parquet_list=[
                    "create_final_nodes.parquet",
                    "create_final_community_reports.parquet",
                    "create_final_text_units.parquet",
                    "create_final_relationships.parquet",
                    "create_final_entities.parquet",
                ]
    graphrag_input_dir_path = os.path.join(address_kdb, "db_files",
                                            "output", "latest", "artifacts")

    if os.path.exists(graphrag_input_dir_path) and os.path.isdir(graphrag_input_dir_path):
        all_files_exist = all(os.path.exists(graphrag_input_dir_path +  "/" +file) for file in parquet_list)
        if all_files_exist:
            graphrag_search = True
        else:
            graphrag_search = False
    else:
        graphrag_search = False

    return {"graphrag_search": graphrag_search}


def permissions_get_allowedExtensions(permissions, if_use_muilt=True):
    allowedExtensions = []
    allowedExtensions = ALLOWEDEXTENSIONS.copy()
    if "multimodal" in permissions and if_use_muilt:
        allowedExtensions += MUlTIMODAL_ALLOWEDEXTENSIONS
    return allowedExtensions

@router.post("/get_allowedExtensions")
async def get_allowedExtensions(request: Request):
    body = await request.json()  # 获取请求体
    permissions = body.get('permissions')
    if_use_muilt = body.get('if_use_muilt')
    allowedExtensions = permissions_get_allowedExtensions(permissions, if_use_muilt)

    print("在kdb中可以的文件后缀权限：",allowedExtensions)
    return {"allowedExtensions": allowedExtensions}


@router.post("/upload_get_allowedExtensions")
async def upload_get_allowedExtensions(request: Request):
    permissions = get_permissions(request)
    allowedExtensions = permissions_get_allowedExtensions(permissions)

    print("在upload中可以的文件后缀权限：",allowedExtensions)
    return {"allowedExtensions": allowedExtensions}


@router.post("/get_current_kdbid")
async def get_current_kdbid(request: SessionRequest):
    session_id = request.session_id
    print("session_id",session_id)
    try:
        # 从 session_mgr 获取 kdb_id
        kdb_id = session_mgr.get_current_kdb(session_id)
        print("Retrieved kdb_id:", kdb_id)

        # 如果没有找到 kdb_id，则返回对应的响应
        if not kdb_id:
            return {"kdb_id": None, "message": "NO kdb_id"}
        return {"kdb_id": kdb_id}

    except Exception as e:
        # 捕获异常并返回错误信息
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/addNewUploadFile", include_in_schema=False)
async def addNewUploadFile(request: Request, files: List[UploadFile] = File(...), fileIds: List[str] = Form(...), session_id: str = Form(...)):
    start_time = time.time()

    user_id = request.cookies.get("current_user")
    for file, file_id in zip(files, fileIds):
        print(file)
        print(f"File ID: {file_id}, File Name: {file.filename}")

    # 获取上传路径
    def_path = get_user_path()
    upload_path = os.path.join(os.path.dirname(def_path),"session", user_id, session_id)
    upload_directory = os.path.join(upload_path, "uploaded_files")
    res_directory = os.path.join(upload_path, "res_files")
    
    # 创建必要的文件夹
    os.makedirs(upload_directory, exist_ok=True)
    os.makedirs(res_directory, exist_ok=True)

    if_use_muilt = True
    current_language = get_current_language(request)

    user_task = {"user_id":user_id,"saved_files":[], "fail_files":[],
                "is_finish":False, "is_error":False, "now_progress":[],"un_analyze_file":[]}

    progress_info[session_id] = user_task

    num_doc = doc_id_db.get_num_session(session_id)

    # 初始化 pipeline
    pipeline = FileProcessPipeline(res_directory)

    # 多模态内容处理
    loop = asyncio.get_event_loop()

    support_multi_modal = True if 'multimodal' in get_permissions(request) else False

    # 定义文件处理函数，支持不定参数
    def process_files(file, doc_id, session_id, file_path, user_task, filename_with_timestamp, support_multi_modal, if_use_muilt, fileId):
        try:
            original_filename = file.filename

            # 保存文件
            print("聊天上传的文件地址：",file_path)
            if os.path.exists(file_path):
                print(f"文件 {file.filename} 已存在, 覆盖")

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # 验证文件是否保存成功
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                print(f"文件保存失败: {file.filename}")
                return None
            else:
                # 记录保存的文件
                user_task.get("saved_files").append(fileId)

                # 使用 Path 对象获取目录，并去掉文件扩展名
                directory_without_extension = Path(file_path).parent / Path(file_path).stem

                # 检查文件夹是否存在并删除
                if os.path.exists(directory_without_extension) and os.path.isdir(directory_without_extension):
                    shutil.rmtree(directory_without_extension)
                    print(f"文件夹 {directory_without_extension} 已删除")

                # 调用 pipeline 处理文件
                outfile = pipeline.process_file(file_path, doc_id, "", current_language, support_multi_modal and if_use_muilt, extract_text=False)
                print("outfile :",outfile)
                if outfile is None:
                    user_task.get("un_analyze_file").append(fileId)
                else:
                    user_task.get("now_progress").append(fileId)
                    session_file_db.addfile(fileId,session_id,original_filename, filename_with_timestamp, file_path, outfile)
                    doc_id_db.add_doc_id(user_id, "", doc_id, original_filename, session_id)

                return outfile

        except Exception as e:
            # 删除文件夹内的文件
            os.remove(file_path)
            # 如果发生任何异常，记录文件并抛出异常
            print(f"处理文件 {file_path} 时发生错误: {e}")
            user_task.get("fail_files").append(fileId)
            return e  # 返回异常对象

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")  # 年月日-小时-分钟-秒

    # 启动任务处理
    with ThreadPoolExecutor() as executor:
        tasks = []
        for index, (file, fileId) in enumerate(zip(files, fileIds)):
            print(f"======文件的名字是 {file.filename} 文件的id是 {fileId}")
            original_filename = file.filename
            filename_with_timestamp = f"{os.path.splitext(original_filename)[0]}-{timestamp}{os.path.splitext(original_filename)[1]}"

            file_path = os.path.join(upload_directory,original_filename)
            
            # 分配文档 ID
            doc_id = num_doc + index +1

            # 提交任务到线程池
            task = loop.run_in_executor(executor, process_files, file, doc_id, session_id, file_path, user_task, filename_with_timestamp, support_multi_modal, if_use_muilt, fileId)
            tasks.append(task)

        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)

        user_task["is_finish"] = True

        finish_time = time.time() - start_time

        print(f"用户 {user_id} 的 {session_id} 的kdb 分析 {len(user_task['saved_files'])} 个文件使用了 {finish_time} s")

        print(f"信息是：{user_task['saved_files']} {user_task['now_progress']}")
        return {"success": True, "session_id": session_id, "file_path": file_path}


@router.post("/input_upload_check")
async def input_upload_check(request: Request):
    body = await request.json()  # 获取请求体
    session_id = body.get('session_id')  # 提取 kdb_date
    print("检测任务中的session",session_id)
    # 检查是否有上传任务
    if session_id not in progress_info:
        print("没有上传任务===============",session_id)
        return {"no_task": True}

    # 有任务，判断是上传完成还是在正上传还是上传失败
    info = progress_info.get(session_id)

    saved_files = info.get("saved_files")
    finish_files = info.get("now_progress")
    fail_files = info.get("fail_files")
    un_analyze_file = info.get("un_analyze_file")
    ng_file = fail_files + un_analyze_file
    if not info.get("is_finish"):
        print(f"用户没有完成分析任务: {info.get('user_id')} 的 kdb: {session_id} 正在分析文件 共有 {len(info.get('saved_files'))} 个文件 已经分析了 {len(info.get('now_progress'))} 个文件")
        no_task = False
    else:
        no_task = True
        print(f"用户完成分析任务: {info.get('user_id')} 的 kdb: {session_id} 正在分析文件 共有 {len(info.get('saved_files'))} 个文件 已经分析了 {len(info.get('now_progress'))} 个文件")

        # 删除记录
        if session_id in progress_info:
            del progress_info[session_id]
            print(f"==================已清除进度信息: {session_id}")
            
    return {"no_task": no_task,"saved_files":saved_files,"finish_file":finish_files,"ng_file":ng_file}


@router.delete("/deleteFile")
async def deleteFile(file_id: str, file_name: str, session_id: str):
    """
    根据给定的 file_id 删除文件记录。

    :param file_id: 要删除的文件的 ID
    :return: 成功消息或错误消息
    """
    print("删除上传文件的id:",file_id)

    # 假设你已经在数据库操作模块里实现了 deletefile 函数F
    upload_file_ad = session_file_db.get_uploaded_file_address(file_id)
    #删除res中的文件
    res_file_ad = session_file_db.get_res_file_address(file_id)

    doc_id_db.delete_doc_id_session(session_id, file_name)

    result = session_file_db.deletefile(file_id)  # 调用删除函数
    if result:
        # 删除文件的文件
        os.remove(Path(upload_file_ad))
        os.remove(Path(res_file_ad))
        return {"success":True,"message": f"文件 {file_id} 删除成功"}
    else:
        return {"success":False,"message": f"文件 {file_id} 删除失败"}



@router.post("/get_node_context")
async def get_node_context(request: Request):
    from kdbmanager import kdbm

    body = await request.json()  # 获取请求体
    kdb_id = body.get('kdb_id')
    node_id = body.get('node_id')

    adrag = await kdbm.create_or_get_rag(kdb_id=kdb_id)
    
    context = adrag.get_node_context(node_id)

    return context


@router.post("/get_session_file")
async def get_session_file(request: Request):
    from kdbmanager import kdbm

    body = await request.json()  # 获取请求体
    session_id = body.get('session_id')
    print("查询的session_id是",session_id)
    file_list = []
    reference_files = await modb_api.get_all_file_record(session_id)
    for reference in reference_files:
        for file_info in reference:
            file_list.append(file_info.get("filename"))

    print("历史的文件是",file_list)

    return file_list