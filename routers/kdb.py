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
from db import user_kdb_mgdb,file_db, user_kdb_info, share_info, doc_id_db,session_mgr
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

# 请求体的数据模型
class FileDownloadRequest(BaseModel):
    kdb_id: str
    filename: str

class SessionRequest(BaseModel):
    session_id: str
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()


@router.get("/showkdb", include_in_schema=False)
async def show_kdb(request: Request):
    response = check_login(request)
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
    response = check_login(request)
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
    return check_login(request) or \
    templates.TemplateResponse("graph/create_kdb.html", {"request": request, "kdb_id": kdb_id, 
                                                                "value": title, "share": share_type, 
                                                                "is_from_share": is_from_share, "permissions": get_permissions(request), 
                                                                "resources": get_resource(request, "create_kdb")})


@router.get("/backShowKdb", include_in_schema=False)
async def backShowKdb(request: Request):
    return check_login(request) or \
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
    


@router.post("/analyze_files")
async def analyze_files(request: Request, data:dict):
    no_analyze = False

    start_time = time.time()

    kdb_id = data.get("kdb_id")
    prompt_name = data.get("prompt_name")
    clean_data = data.get("clean_data")
    file_names = data.get("file_names")

    if not file_names:
        return {"is_an":False,"message": "没有找到需要分析的文件"}
    
    user_id = request.cookies.get("current_user")

    UPLOAD_PATH = get_user_path()

    upload_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "uploaded_files")

    uploaded_files = [ os.path.join(upload_directory, file_nmae) for file_nmae in file_names]

    print("文件的地址：",uploaded_files)

    resource = get_resource(request, "create_kdb")

    print(f"开始分析文件, prompt_name: {prompt_name}, kdb_id: {kdb_id}, clean_data: {clean_data} 上传的文件有: {file_names}")

    current_language = request.cookies.get("current_language")
    # 通过current_language获得语言
    if not current_language:
        # 从请求头中提取 'Accept-Language'
        current_language = request.headers.get("accept-language")
        if current_language:
            # 解析 'Accept-Language' 获取首选语言
            current_language = [lang.split(";")[0].strip() for lang in current_language.split(",")][0]
    print("上传文件获得到的最终的语言是：",current_language)

    # 初始化路径
    res_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "res_files")
    os.makedirs(res_directory, exist_ok=True)

    # 初始化任务
    pipeline = FileProcessPipeline(res_directory)
    kdb = kdbm.create_or_get_rag(kdb_id=kdb_id)

    num_doc = user_kdb_info.get_kdb_doc(kdb_id)
    
    user_task = {"user_id":user_id,"saved_files":file_names, "fail_files":[],
                  "is_finish":False, "is_error":False, "now_progress":[],"un_analyze_file":[]}
    progress_info[kdb_id] = user_task
    print("上传任务：", progress_info)

    len_file = 0

    delete_len = 0

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
            def process_file_wrapper(file_path, doc_id, prompt_name, user_id, kdb_id, filename, user_task):
                try:
                    # 检查是否已经有保存图片的文件
                    # 使用 Path 对象获取目录，并去掉文件扩展名
                    directory_without_extension = Path(file_path).parent / Path(file_path).stem
                    
                    # 检查文件夹是否存在
                    if os.path.exists(directory_without_extension) and os.path.isdir(directory_without_extension):
                        # 删除文件夹及其内容
                        shutil.rmtree(directory_without_extension)
                        print(f"文件夹 {directory_without_extension} 已删除")

                    support_multi_modal = True if 'multimodal' in get_permissions(request) else False
                    outfile = pipeline.process_file(file_path, doc_id, prompt_name, current_language, support_multi_modal, extract_text=False)

                    # 更新进度
                    user_task.get("now_progress").append(filename)

                    # 如果处理失败，删除文件并记录失败文件
                    if outfile is None:
                        user_task.get("un_analyze_file").append(os.path.basename(file_path))
                    else:
                        doc_id_db.add_doc_id(user_id, kdb_id, doc_id, filename)
                    return outfile
                
                except Exception as e:
                    # 如果发生任何异常，记录文件并抛出异常
                    user_task["is_error"] = True
                    user_task.get("fail_files").append(os.path.basename(file_path))
                    print(f"处理文件 {file_path} 时发生错误: {e}")
                    return e  # 返回异常对象

            # 分配文档 ID
            doc_id = num_doc + len_file

            # 提交任务到线程池
            task = loop.run_in_executor(executor, process_file_wrapper, file_path, doc_id, prompt_name, user_id, kdb_id, file_name, user_task)
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
                    os.remove(file_path)  # 删除文件
            else:
                # 确保结果为有效路径
                if result is None:
                    delete_len -= 1  # 文件处理失败时，减少 len_file 的值
                    os.remove(file_path)
                else:
                    await kdb.add_document(file_path=result)

        change_source(user_id, kdb_id, delete_len, 0)
        user_task["is_finish"] = True


@router.get("/analyze_files_ad")
async def analyze_files_ad(request: Request):
    no_analyze = False
    start_time = time.time()

    # 从查询参数中获取数据
    kdb_id = request.query_params.get("kdb_id")
    prompt_name = request.query_params.get("prompt_name")
    address = request.query_params.get("address")  # 获取多个文件名
    print("prompt_name",prompt_name)
    if not address:
        return {"is_an":False,"message": "没有找到需要分析的文件"}
    
    def get_files_in_directory(directory_path):
        # 获取目录下的所有文件和文件夹
        files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        return files

    file_names = get_files_in_directory(address)
    print("文件的名字：",file_names)
    
    user_id = request.cookies.get("current_user")

    UPLOAD_PATH = get_user_path()

    uploaded_files = [ os.path.join(address, file_nmae) for file_nmae in file_names]

    print("文件的地址：",uploaded_files)

    resource = get_resource(request, "create_kdb")


    current_language = request.cookies.get("current_language")
    # 通过current_language获得语言
    if not current_language:
        # 从请求头中提取 'Accept-Language'
        current_language = request.headers.get("accept-language")
        if current_language:
            # 解析 'Accept-Language' 获取首选语言
            current_language = [lang.split(";")[0].strip() for lang in current_language.split(",")][0]
    print("上传文件获得到的最终的语言是：",current_language)

    # 初始化路径
    res_directory = os.path.join(UPLOAD_PATH, user_id, kdb_id, "res_files")
    os.makedirs(res_directory, exist_ok=True)

    # 初始化任务
    pipeline = FileProcessPipeline(res_directory)
    kdb = kdbm.create_or_get_rag(kdb_id=kdb_id)

    num_doc = user_kdb_info.get_kdb_doc(kdb_id)
    
    user_task = {"user_id":user_id,"saved_files":file_names}
    progress_info[kdb_id] = user_task
    print("上传任务：", progress_info)

    len_file = 0

    delete_len = 0
    try:
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
                def process_file_wrapper(file_path, doc_id, prompt_name, user_id, kdb_id, filename):
                    # 检查是否已经有保存图片的文件
                    # 使用 Path 对象获取目录，并去掉文件扩展名
                    directory_without_extension = Path(file_path).parent / Path(file_path).stem
                    
                    # 检查文件夹是否存在
                    if os.path.exists(directory_without_extension) and os.path.isdir(directory_without_extension):
                        # 删除文件夹及其内容
                        shutil.rmtree(directory_without_extension)
                        print(f"文件夹 {directory_without_extension} 已删除")
                    else:
                        print(f"文件夹 {directory_without_extension} 不存在")

                    support_multi_modal = True if 'multimodal' in get_permissions(request) else False
                    outfile = pipeline.process_file(file_path, doc_id, prompt_name, current_language, support_multi_modal, extract_text=False)
                    # 如果是空则删除upload上的文件
                    if not outfile:
                        os.remove(file_path)
                    else:
                        doc_id_db.add_doc_id(user_id, kdb_id, doc_id, filename)

                    return outfile

                # 分配文档 ID
                doc_id = num_doc + len_file

                # 提交任务到线程池
                task = loop.run_in_executor(executor, process_file_wrapper, file_path, doc_id, prompt_name, user_id, kdb_id, file_name)
                tasks.append(task)


            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 遍历每个任务的结果，如果处理成功（outfile 非空），则分配文档 ID
            for outfile in results:
                if not outfile:
                    # 如果处理失败，减小 len_file
                    delete_len -= 1  # 文件处理失败时，减少 len_file 的值
                    
            # 处理结果
            for file_path, result in zip(uploaded_files, results):
                if isinstance(result, Exception):
                    # 删除已保存的文件，处理异常
                    if os.path.exists(file_path):
                        os.remove(file_path)  # 删除文件
                    raise result  # 抛出异常
                else:
                    # 确保结果为有效路径
                    if result is None or not os.path.isfile(result):
                        continue
                    await kdb.add_document(file_path=result)

    except Exception as e:
        print(f"发生错误: {str(e)}")
        no_analyze = True
        # 确保删除任务记录
        if kdb_id in progress_info:
            del progress_info[kdb_id]
            print(f"已清除进度信息: {kdb_id}")

        return {"no_analyze":True,"message": f"{resource.get('upload_fail')}!"}

    finally:
        # 更新源信息
        if not no_analyze:
            end_time = time.time() - start_time
            print("######################################")
            print(f"user: {user_id} 的 kdb: {kdb_id} 分析了 {len_file} 个文件, 有 {delete_len} 个文件发生了错误 花费了 {end_time}")
            print("######################################")
            # 减少文件的数量
            print("文件处理的错误数量：",delete_len)
            change_source(user_id, kdb_id, delete_len, 0)        
            # 确保删除任务记录
            if kdb_id in progress_info:
                del progress_info[kdb_id]
                print(f"已清除进度信息: {kdb_id}")

            if delete_len:
                return {"no_analyze": False, "message": f"{resource.get('successful_analysis')} {len_file} {resource.get('get_file')} \
                        {resource.get('have')} {delete_len} {resource.get('get_file')} {resource.get('un_anz')}"}

            return {"no_analyze": False, "message": f"{resource.get('successful_analysis')} {len_file} {resource.get('get_file')}"}




@router.post("/files")
async def list_files(request: Request, kdb_id_data: dict):
    kdb_id = kdb_id_data.get("kdb_id")  # 从字典中提取 kdb_id
    address = user_kdb_mgdb.get_address(kdb_id)["address"]
    upload_directory = os.path.join(address, "uploaded_files")

    if not os.path.isdir(upload_directory):
        return []

    files = []
    for filename in os.listdir(upload_directory):
        file_path = os.path.join(upload_directory, filename)
        if os.path.isfile(file_path):
            files.append(filename)
    return files


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

        rag_search = True if len(os.listdir(res_directory)) > 0 else False

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
            kdb = kdbm.create_or_get_rag(kdb_id=kdb_id)

            await kdb.build_knowledge_base(res_directory)

            return {"build": True, "message": f"{resource.get('successful_rebuild_rag')}!"}

        return {"build": False, "message": f"{resource.get('fail_rag_mes')}！"}



@router.post("/get_kdb_title")
async def get_kdb_title(request: Request, kdb_id: dict):
    import pandas as pd
    import numpy as np
    from db import user_kdb_mgdb

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
async def download_file(request: Request, file_request: FileDownloadRequest):
    filename = file_request.filename
    kdb_id = file_request.kdb_id

    user_dir_path = user_kdb_mgdb.get_address(kdb_id)["address"]
    file_path = os.path.join(user_dir_path, "uploaded_files", filename)

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
async def get_image(image_name: str, doc_id: str, kdb_id: str):
    # 获取默认路径
    print("kdb_id",kdb_id)
    print("doc_id",doc_id)
    file_path, user_id = doc_id_db.get_file_name(kdb_id, int(doc_id))
    default_path=get_user_path()
    from urllib.parse import unquote
    image_name = unquote(image_name)
    print(" image_name :",image_name)
    print("file_path :",file_path)
    if not file_path:
        return
    if not image_name.endswith(file_path):
        file_path, _ = os.path.splitext(file_path)
        # 拼接文件的完整路径
        image_path = os.path.join(str(default_path), str(user_id), str(kdb_id), "uploaded_files", str(file_path), str(image_name))
    else:
        image_path = os.path.join(str(default_path), str(user_id), str(kdb_id), "uploaded_files", str(file_path))
    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    # 返回图片文件
    return FileResponse(image_path)


@router.post("/check_el_pr_res_up")
async def build_check(request: Request):
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
    rag_res_directory = os.path.join(address_kdb, "res_files")

    if os.path.exists(rag_res_directory) and os.path.isdir(rag_res_directory):
        if len(os.listdir(rag_res_directory)) > 0:
            rag_search = True
        else:
            rag_search = False
    else:
        rag_search = False


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

    # if info.get("is_error"):
    #     # 删除记录
    #     if kdb_id in progress_info:
    #         del progress_info[kdb_id]
    #         print(f"已清除进度信息: {kdb_id}")
    #     fail_files = info.get("fail_files")
    #     if len(fail_files) != 0:
    #         print("分析文件发生错误")
    #         mes = resource.get('file') + " "
    #         for i in fail_files:
    #             mes += (i + " ")
    #         mes += (resource.get('file_fail') + "," + resource.get('an_again') + "!")
    #         print("错误信息：",mes)
    #         return {"no_task":True,"mesaage": mes}
    #     return {"no_task": True, "mesaage":resource.get("upload_fail")+"!"}
    """
        user_task = {"user_id":user_id,"saved_files":file_names, "fail_files":[],
                  "is_finish":False, "is_error":False, "now_progress":[],"un_analyze_file":[]}
    """
    if not info.get("is_finish"):
        print(f"用户: {info.get('user_id')} 的 kdb: {kdb_id} 正在分析文件 共有 {len(info.get('saved_files'))} 个文件 已经分析了 {len(info.get('now_progress'))} 个文件")
        saved_files = info.get("saved_files")
        finish_files = info.get("now_progress")
        return {"no_task": False,"saved_files":saved_files,"finish_file":finish_files}
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
            mes_error += (resource.get('file_error') or "" + " ")

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
async def upload_check(request: Request):
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


@router.post("/get_allowedExtensions")
async def upload_check(request: Request):
    body = await request.json()  # 获取请求体
    permissions = body.get('permissions')
    print("permissions:",permissions)
    allowedExtensions = []
    allowedExtensions = ALLOWEDEXTENSIONS.copy()
    if "multimodal" in permissions:

        allowedExtensions += MUlTIMODAL_ALLOWEDEXTENSIONS

    print("可以的文件后缀权限：",allowedExtensions)
    return {"allowedExtensions": allowedExtensions}


@router.post("/get_current_kdbid")
async def get_session_kdb_id(request: SessionRequest):
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
