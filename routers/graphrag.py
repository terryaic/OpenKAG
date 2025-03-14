from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pathlib import Path
from graphrag.api.index import get_index
import uuid
from pydantic import BaseModel, FilePath
from typing import Optional
# routers/graphrag.py
from fastapi import APIRouter
import os
from starlette.templating import Jinja2Templates
from db import user_kdb_mgdb
import pandas as pd
import numpy as np
from apis.version1.route_login import get_resource


templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

g_user_path = None
def set_user_path(user_path):
    global g_user_path
    g_user_path = user_path

def get_user_path():
    return g_user_path

router = APIRouter()

class DownloadRequest(BaseModel):
    root_directory: Optional[FilePath] = 'stores/default/db_files'
    config_file: Optional[FilePath] = 'stores/default/db_files/settings.yaml'
    run_identifier: Optional[str] = 'latest'
    is_update_run: Optional[bool] = False


# 存储下载状态和进度队列
# download_queues = {} 
download_queues = {"information":[]} 
is_update = {}

# 修改图谱的列的名字
# human_readable_id	title type description
# human_readable_id	source	target	description	weight	combined_degree

column_mapping_cn = {"title": "名字","type": "类型","description": "描述", "source": "源节点","target": "目标节点",
                        "rank": "等级","weight": "权重","human_readable_id": "索引",
                        "combined_degree": "连接度数","Related":"关联"}

column_mapping_en = {"title": "name","type": "type","description": "description","human_readable_id": "human_readable_id",
                        "source": "source","target": "target","rank": "rank","weight": "weight",
                        "combined_degree": "combined_degree","Related":"Related"}

def get_column_mapping(request: Request):
    language = get_current_language(request).get("language")
    if language == "zh" or language == "zh-CN" or language == "zh-TW" or language == "zh-HK":
        return column_mapping_cn
    return column_mapping_en


# 存储下载任务信息的类
class DownloadTask:
    def __init__(self, session_id: str, progress_queue: asyncio.Queue):
        self.session_id = session_id
        self.workflow_name = None
        self.num_workflows = 0
        self.finished_workflows = 0
        self.now_workflow = 0
        self.progress = 0
        self.progress_queue = progress_queue
        self.is_downloading= None
        self.is_stop = False
        self.is_graceful_stop = None
        self.complete_finish = None

    def update_mes(self, workflow_name: str, num_workflows: int, finished_workflows: int, now_workflow: int):
        self.workflow_name = workflow_name
        self.num_workflows = num_workflows
        self.finished_workflows = finished_workflows
        self.now_workflow = now_workflow
        self.progress = round(finished_workflows / num_workflows * 100, 2)

    def start(self):
        self.is_downloading = True

    def stop(self):
        self.is_stop = True

    def finish(self):
        self.is_downloading = False

    def complete_finished(self):
        self.complete_finish = True

    def graceful_stop(self):
        self.is_graceful_stop = True
        self.complete_finish = False

def get_files_in_folder(folder_path):
    """获取文件夹中的文件列表（只获取文件，不包含子文件夹）"""
    return {f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))}


@router.post("/check_res_file")
async def check_res_file(request: Request, kdb_id: dict):
    import os
    user_id = request.cookies.get("current_user")
    kdb_id = kdb_id.get("kdb_id")
    root_directory = os.path.join(get_user_path(), user_id, kdb_id)
    
    import shutil

    res_file_path = os.path.join(root_directory, "res_files")
    res_file_names = get_files_in_folder(res_file_path)

    input_folder_path = os.path.join(root_directory, "db_files", 'input')
    os.makedirs(input_folder_path, exist_ok=True)
    input_file_names = get_files_in_folder(input_folder_path)

    if len(res_file_names) == 0 and len(input_file_names) == 0:
        return {"error": True}

    if len(res_file_names) == 0:
        return {"start": False}

    #当为空和非空的情况
    if len(input_file_names) == 0:
        #则直接添加，开始运行
        shutil.copytree(res_file_path, input_folder_path,dirs_exist_ok=True)
        return {"start": True}
    else:
        # input有文件 查看是否有新的文件或减少的文件
        new_files = res_file_names - input_file_names
        deleted_files = input_file_names - res_file_names

        if len(new_files) > 0 or len(deleted_files) > 0:
            #有新增的文件
            #传送文件
            shutil.rmtree(input_folder_path)
            #删除原来的文件
            shutil.copytree(res_file_path, input_folder_path,dirs_exist_ok=True)
            if len(new_files) > 0 and len(deleted_files) == 0:
                is_update[kdb_id] = True
            else:
                is_update[kdb_id] = False
            return {"start": True}
        else:
            is_update[kdb_id] = False
            return {"start": False}
        
def get_current_language(request: Request):
    # 尝试从 Cookies 中获取语言
    language = request.cookies.get("current_language")
    print("页面的语言:",language)
    if not language:
        # 从请求头中提取 'Accept-Language'
        accept_language = request.headers.get("accept-language")
        if accept_language:
            # 解析 'Accept-Language' 获取首选语言
            languages = [lang.split(";")[0].strip() for lang in accept_language.split(",")]
            return {"language": languages[0]}
    return {"language": language or "zh-CN"}  # 默认返回英文


@router.post("/start_rebuiltGraph")
async def start_download(request: Request, kdb_id: dict):
    user_id = request.cookies.get("current_user")
    kdb_id = kdb_id.get("kdb_id")
    

    resource = get_resource(request, "create_kdb")

    import os
    if request is None:
        request = DownloadRequest()  # 创建一个带有默认值的实例

    root_directory = os.path.join(get_user_path(), user_id, kdb_id, "db_files")
    config_file = os.path.join(root_directory, "settings.yaml")

    session_id = str(uuid.uuid4())  # 生成一个新的 session_id

    run_identifier = 'latest'

    is_update_run = is_update.get(kdb_id)

    progress_queue = asyncio.Queue()

    download_task = DownloadTask(
        session_id=session_id,
        progress_queue=progress_queue
    )

    info = {"user_id": user_id, "kdb_id": kdb_id, "session_id": session_id, "download_task": download_task}
    download_queues["information"].append(info)

    download_task.start()

    # 启动异步任务，不会阻塞 API 响应
    asyncio.create_task(get_index(download_task, root_directory, config_file, run_identifier,is_update_run))
    return {"message": resource.get("start_build"), "session_id": session_id}

@router.post("/check_progress")
async def check_progress(request: Request):
    user_id = request.cookies.get("current_user")
    data = await request.json()
    kdb_id = data["kdb_id"]
    info = download_queues["information"]
    download_task = None
    print("下载任务",info)
    for i in info:
        if i["user_id"] == user_id and i["kdb_id"] == kdb_id:
            dowmload_info = i
            download_task = i.get("download_task")
            if download_task:
                # 判断是否已经下载完成或者停止完成

                progress = download_task.progress

                #下载完成
                if progress >= 100:
                    download_queues["information"].remove(dowmload_info)
                    return {"have_task": False}

                #是否停止完成
                if download_task.is_graceful_stop:
                    download_queues["information"].remove(dowmload_info)
                    return {"have_task": False}
                
                is_stop = download_task.is_stop
                if is_stop:
                    #点了暂停，但还没完全停止
                    return {"have_task": True, "is_stop":is_stop}
                else:
                    #下载任务没有完成，没有停止
                    return {"have_task": True, "is_stop":is_stop}

            break

    return {"have_task": False}


@router.post("/progress")
async def get_progress(request: Request):
    user_id = request.cookies.get("current_user")
    data = await request.json()
    kdb_id = data["kdb_id"]
    session_id = data["session_id"]
    info = download_queues["information"]

    dowmload_info = {}

    download_task = None

    resource = get_resource(request, "create_kdb")


    if len(info) == 0:
        return JSONResponse(content={"is_rebuild": False, "error": "没有下载任务"})


    if session_id:
        for i in info:
            if i["session_id"]== session_id:
                dowmload_info = i
                download_task = i.get("download_task")
                break
    else:
        for i in info:
            if i["user_id"]== user_id and i["kdb_id"]== kdb_id:
                dowmload_info = i
                download_task = i.get("download_task") 
                break


    if not download_task:
        return JSONResponse(content={"no_task": True, "message": resource.get('no_build_task')})

    if download_task.is_graceful_stop:
        download_queues["information"].remove(dowmload_info)
        return JSONResponse(content={"is_rebuild": False, "progress": resource.get('task_stop_successful')})
    

    workflow_name = download_task.workflow_name
    now_workflow = download_task.now_workflow 
    progress = download_task.progress
    num_workflows = download_task.num_workflows

    print("用户名字：",user_id)
    print("kdb名字",kdb_id)
    print("任务名字：",workflow_name)
    print("现在任务：",now_workflow)
    print("任务状态：",progress)
    print("任务总数：",num_workflows)


    if download_task.complete_finish:
        download_queues["information"].remove(dowmload_info)
        return JSONResponse(content={
            "is_rebuild": False,
            "progress": progress,
            "workflow_name": workflow_name,
            "now_workflow": now_workflow,
            "num_workflows": num_workflows
        })

    return JSONResponse(content={
        "is_rebuild": True,
        "progress": progress,
        "workflow_name": workflow_name,
        "now_workflow": now_workflow,
        "num_workflows": num_workflows
    })


@router.post("/stop_rebuiltGraph")
async def stop_download(request: Request):
    data = await request.json()
    kdb_id = data["kdb_id"]
    session_id = data["session_id"]
    resource = get_resource(request, "create_kdb")
    download_task = None
    if session_id:
        for i in download_queues["information"]:
            if i["session_id"] == session_id:
                download_task = i.get("download_task")
                break
    else:
        for i in download_queues["information"]:
            if i["kdb_id"]== kdb_id:
                download_task = i.get("download_task") 

    if download_task:
        if download_task.is_stop:
            return JSONResponse(content={"type": "mul_stop", "message": resource.get('first_stop')})
        download_task.stop()
        return JSONResponse(content={"type": "first_stop", "message": resource.get('wait_stop')})
    else:
        return JSONResponse(content={"error": "无效的 session ID"}, status_code=404)
    


@router.post("/local_data")
async def get_data(request: Request, kdb_id: dict):
    from db import user_kdb_mgdb
    
    user_id = request.cookies.get("current_user")
    kdb_id = kdb_id.get("kdb_id")  # 从字典中提取 kdb_id
    language = request.cookies.get("current_language")
     # 通过current_language获得语言
    if not language:
        # 从请求头中提取 'Accept-Language'
        language = request.headers.get("accept-language")
        if language:
            # 解析 'Accept-Language' 获取首选语言
            language = [lang.split(";")[0].strip() for lang in language.split(",")][0]
    print("上传文件获得到的最终的语言是：",language)

    address = user_kdb_mgdb.get_address(kdb_id)
    ad = address["address"]
    graphrag_input_dir_path = ad + "/db_files/output/latest/artifacts"

    #判断是否有数据库信息
    if not (os.path.isfile(os.path.join(graphrag_input_dir_path, "create_final_relationships.parquet")) and os.path.isfile(os.path.join(graphrag_input_dir_path, "create_final_entities.parquet"))):
        return {"is_show": False}
    
    # 假设 GRAPHRAG_FOLDER 已定义并指向正确的目录
    # human_readable_id	source	target	description	weight	combined_degree

    rel_df = pd.read_parquet(f'{graphrag_input_dir_path}/create_final_relationships.parquet',
                            columns=["source","target","weight","human_readable_id","description","combined_degree"])
    # 将信息转换为对应的文字
    column_mapping = get_column_mapping(request)
    rel_df = rel_df.rename(columns=column_mapping)

    source_degree = {}

    # 创建适合 ECharts 的 links
    links = []
    for index, row in rel_df.iterrows():
        link = {
            'source': row[column_mapping.get('source')],  # 源节点名称
            'target': row[column_mapping.get('target')],  # 目标节点名称
            'name': column_mapping.get("Related"),  # 关系展示的前端
            'info': row.to_dict(),  # 关系描述 需要移动到对应位置的
            'des': row.to_dict().get(column_mapping.get('description')),
        }
        links.append(link)
        source_degree[row[column_mapping.get('source')]] = row[column_mapping.get('combined_degree')]

    #读取实体
    # human_readable_id	title type description

    entity_df = pd.read_parquet(f'{graphrag_input_dir_path}/create_final_entities.parquet', 
                                columns=["title","type","description","human_readable_id"])

    entity_df = entity_df.rename(columns=column_mapping)

    # 提取唯一的 type 值并创建类型到类别的映射
    unique_types = entity_df[column_mapping.get('type')].unique()
    type_to_category = {type_name: idx for idx, type_name in enumerate(unique_types)}
    # 创建字典并将 unique_types 转换为列表
    result_types = unique_types.tolist()

    min_symbolSize = 50
    max_symbolSize = 100

    min_size = max_symbolSize
    max_size = min_symbolSize

    # 创建适合 ECharts 的 nodes
    nodes = []
    for index, row in entity_df.iterrows():
        # 根据 type 字段设置类别
        category = type_to_category[row[column_mapping.get('type')]]
        node_source_degree = source_degree.get(row[column_mapping.get('title')])

        if not node_source_degree:
            node_size = min_symbolSize
        else:
            node_size = min_symbolSize + int(np.tanh(node_source_degree) * (max_symbolSize - min_symbolSize))

        min_size = node_size if node_size < min_size else min_size
        max_size = node_size if node_size > max_size else max_size

        node = {
            'name': row[column_mapping.get('title')],
            'info': row.to_dict(),
            'des': row.to_dict().get(column_mapping.get('description')),
            'symbolSize': node_size,  # 可以根据需要调整
            'category': category  # 根据 type 设置类别
        }
        nodes.append(node)

    init_show_size = int(0.9 * max_size)

    info_json = get_resource(request,"create_kdb")

    entity_title = info_json.get("entity_info")
    relationship_title = info_json.get("relationship_info")

    return {"is_show": True, "nodes": nodes, "links": links, "unique_types":result_types, 
            "symbolSize": {"max_size": max_size, "min_size": min_size, "init_show_size": init_show_size},
            "entity_title":entity_title,"relationship_title":relationship_title}



# 定义请求体模型
class ER_RequestModel(BaseModel):
    kdb_id: str
    id: str


@router.post("/local_entity")
async def get_entity(request:Request, data: ER_RequestModel):

    from db import user_kdb_mgdb

    kdb_id = data.kdb_id
    id_json = data.id
    address = user_kdb_mgdb.get_address(kdb_id)
    language = request.cookies.get("current_language")

    ad = address["address"]
    graphrag_input_dir_path = ad + "/db_files/output/latest/artifacts"
    #读取实体
    # human_readable_id	title type description

    entity_df = pd.read_parquet(f'{graphrag_input_dir_path}/create_final_entities.parquet', 
                                columns=["title","type","description","human_readable_id"])
    column_mapping = get_column_mapping(request)
    entity_df = entity_df.rename(columns=column_mapping)

    # 提取唯一的 type 值并创建类型到类别的映射
    # 查找指定 ID 的数据
    result = entity_df.loc[entity_df[column_mapping.get('human_readable_id')] == int(id_json)]
    result = result.to_dict()

    try:
        result = {
            key: value[list(value.keys())[0]] if value and list(value.keys()) else "null"
            for key, value in result.items()
        }
    except Exception as e:
        print(f"Error occurred during processing: {e}")
        # 可根据需求返回错误信息或中止处理
        result = {}

    return result


@router.post("/local_relationship")
async def get_relationship(request:Request, data: ER_RequestModel):

    from db import user_kdb_mgdb

    kdb_id = data.kdb_id
    id_json = data.id
    address = user_kdb_mgdb.get_address(kdb_id)
    ad = address["address"]
    graphrag_input_dir_path = ad + "/db_files/output/latest/artifacts"
    language = request.cookies.get("current_language")
    print("id:",id_json)


    # 假设 GRAPHRAG_FOLDER 已定义并指向正确的目录
    # human_readable_id	source	target	description	weight	combined_degree

    rel_df = pd.read_parquet(f'{graphrag_input_dir_path}/create_final_relationships.parquet',
                            columns=["source","target","weight","human_readable_id","description","combined_degree"])
    column_mapping = get_column_mapping(request)
    rel_df = rel_df.rename(columns=column_mapping)

    result = rel_df.loc[rel_df[column_mapping.get('human_readable_id')]== int(id_json)]
    print("relationship:",result)
    result = result.to_dict()
    try:
        result = {
            key: value[list(value.keys())[0]] if value and list(value.keys()) else "null"
            for key, value in result.items()
        }
    except Exception as e:
        print(f"Error occurred during processing: {e}")
        # 可根据需求返回错误信息或中止处理
        result = {}
    return result


# 定义请求体模型
class RequestModel(BaseModel):
    kdb_id: str
    id_json: dict

def convert_keys_to_int(d):
        new_dict = {}
        for k, v in d.items():
            # 将键转换为int
            new_key = int(k) if isinstance(k, str) and k.isdigit() else k
            # 如果值是字典，递归调用
            if isinstance(v, dict):
                new_dict[new_key] = convert_keys_to_int(v)
            else:
                new_dict[new_key] = v
        return new_dict

@router.post("/get_nl")
async def get_nl(request: Request, data: RequestModel):
    kdb_id = data.kdb_id
    id_json = data.id_json
    language = request.cookies.get("current_language")

    column_mapping = get_column_mapping(request)

    def merge_dictionaries(dict1, dict2, conflict_resolution='dict1'):
        from collections import defaultdict
        """
        合并两个嵌套字典。
        
        参数：
            dict1 (dict): 第一个字典。
            dict2 (dict): 第二个字典。
            conflict_resolution (str): 冲突解决策略，默认为 'dict1'。选项：
                - 'dict1'：保留第一个字典的值。
                - 'dict2'：保留第二个字典的值。
        
        返回：
            dict: 合并后的字典。
        """
        merged_dict = defaultdict(dict)

        # 将第一个字典内容添加到merged_dict
        for key in dict1:
            for sub_key, value in dict1[key].items():
                merged_dict[key][sub_key] = value

        # 将第二个字典内容合并到merged_dict
        for key in dict2:
            for sub_key, value in dict2[key].items():
                if sub_key in merged_dict[key]:
                    # 处理冲突
                    if merged_dict[key][sub_key] != value:
                        if conflict_resolution == 'dict2':
                            merged_dict[key][sub_key] = value
                else:
                    # 若不存在冲突，直接添加
                    merged_dict[key][sub_key] = value

        # 转换为普通字典并返回
        return dict(merged_dict)
    try:
        address = user_kdb_mgdb.get_address(kdb_id)
        ad = address["address"]
        graphrag_input_dir_path = ad + "/db_files/output/latest/artifacts"

        entity_josn = id_json.get("entity")
        relationship_json = id_json.get("relationship")

        if not entity_josn and not relationship_json:
            return {"is_show":False}
        
        if len(entity_josn) == 0 and len(relationship_json) == 0:
            return {"is_show":False}

        if not relationship_json:
            source_degree = {}
            links = []
        else:
            if len(relationship_json) == 0:
                source_degree = {}
                links = []
            else:
                relationship_list = []
                for i in relationship_json:
                    relationship_list.append(int(i["id"]))
            
                # entities 来自人relationship的source和target
                entites_name = []

                # 假设 GRAPHRAG_FOLDER 已定义并指向正确的目录
                # human_readable_id	source	target	description	weight	combined_degree
                rel_df = pd.read_parquet(f'{graphrag_input_dir_path}/create_final_relationships.parquet',
                                        columns=["source","target","weight","human_readable_id","description","combined_degree"])
                rel_df = rel_df.rename(columns=column_mapping)
                relationship = rel_df.loc[rel_df[column_mapping.get('human_readable_id')].isin([i for i in relationship_list])]
                source_degree = relationship.set_index(column_mapping.get('source'))[column_mapping.get('combined_degree')].to_dict()
                relationship_dict = relationship.to_dict()
                relationship_dict = convert_keys_to_int(relationship_dict)
                relationship_list = list(relationship_dict.get(column_mapping.get('source')).keys())
                # 创建适合 ECharts 的 links
                links = []
                for i in relationship_list:
                    inf = {}
                    for k,v in relationship_dict.items():
                        inf[k] = v[i]
                    link = {
                        'source': relationship_dict[column_mapping.get('source')][i],  # 源节点名称
                        'target': relationship_dict[column_mapping.get('target')][i],  # 目标节点名称
                        'name': column_mapping.get('Related'),  # 关系展示的前端
                        'info': inf,  # 关系描述 需要移动到对应位置的
                        'des': inf.get(column_mapping.get('description')),  # 关系描述 需要移动到对应位置的
                    }
                    entites_name.append(str(relationship_dict[column_mapping.get('source')][i]))
                    entites_name.append(str(relationship_dict[column_mapping.get('target')][i]))

                    links.append(link)


        entity_list = []
        for i in entity_josn:
            entity_list.append(int(i["id"]))

        #读取实体
        # human_readable_id	title type description
        entity_df = pd.read_parquet(f'{graphrag_input_dir_path}/create_final_entities.parquet', 
                                    columns=["title","type","description","human_readable_id"])
        entity_df = entity_df.rename(columns=column_mapping)
        # 提取唯一的 type 值并创建类型到类别的映射
        entities = entity_df.loc[entity_df[column_mapping.get('human_readable_id')].isin(entity_list)]
        entities_from_name = entity_df.loc[entity_df[column_mapping.get('title')].isin(entites_name)]

        entities_dict = entities.to_dict()
        entities_dict = convert_keys_to_int(entities_dict)

        entities_from_name = entities_from_name.to_dict()
        entities_from_name = convert_keys_to_int(entities_from_name)

        final_entites = merge_dictionaries(entities_dict, entities_from_name, conflict_resolution='dict1')

        result_types = list(set(final_entites[column_mapping.get('type')].values()))

        min_symbolSize = 50
        max_symbolSize = 100

        min_size = max_symbolSize
        max_size = min_symbolSize

        type_to_category = {type_name: idx for idx, type_name in enumerate(result_types)}

        loc_list = list(final_entites[column_mapping.get('human_readable_id')].keys())

        # 创建适合 ECharts 的 nodes
        nodes = []
        for j in loc_list:
            # 根据 type 字段设置类别
            category = type_to_category[final_entites[column_mapping.get('type')][j]]
            node_source_degree = source_degree.get(final_entites[column_mapping.get('title')][j])

            if not node_source_degree:
                node_size = min_symbolSize
            else:
                node_size = min_symbolSize + int(np.tanh(node_source_degree) * (max_symbolSize - min_symbolSize))

            min_size = node_size if node_size < min_size else min_size
            max_size = node_size if node_size > max_size else max_size

            inf_enetity = {}
            for k,v in final_entites.items():
                inf_enetity[k] = v[j]
            node = {
                'name': final_entites[column_mapping.get('title')][j],
                'info': inf_enetity,
                'des': inf_enetity.get(column_mapping.get('description')),
                'symbolSize': node_size,  # 可以根据需要调整
                'category': category  # 根据 type 设置类别
            }
            nodes.append(node)

        init_show_size = min_size

        info_json = get_resource(request,"create_kdb")

        entity_title = info_json.get("entity_info")
        relationship_title = info_json.get("relationship_info")

    except Exception as e:
        return {"error": f"未知错误: {str(e)}","is_show":False}
    
    return {"is_show":True, "nodes": nodes, "links": links, "unique_types":result_types, 
        "symbolSize": {"max_size": max_size, "min_size": min_size, "init_show_size": init_show_size},
                    "entity_title":entity_title,"relationship_title":relationship_title}


@router.post("/get_prompt")
async def get_prompt(text_josn: dict):
    text = text_josn.get("text")

    if not text:
        return {"question":{}}
    
    from sysprompts import GRAPHRAG_GET_JSON_CN
    data = GRAPHRAG_GET_JSON_CN
    # 使用 f-string 替换
    formatted_data = data.replace("{text}", text)

    return {"question":formatted_data}




@router.post("/get_el_name")
async def get_el_name(info_josn:dict):
    """
    input:
            {
                "entity": [
                    {"id": 90},
                    {"id": 65}
                ],
                "relationship": [
                    {"id": 94},
                    {"id": 125},
                    {"id": 139}
                ],
                "sources": []
            }
    return: {"ef_id": , "entity_name": , "relationship_name": }
    """
    kdb_id = info_josn.get('kdb_id')  # 提取 kdb_date
    id_json = info_josn.get('id_json')  # 提取 kdb_date
    print("id信息:", id_json)
    entity_josn = id_json.get("entity")
    relationship_json = id_json.get("relationship")
    print("entity_josn",entity_josn)
    print("relationship_json",relationship_json)

    if kdb_id:
        ad = user_kdb_mgdb.get_address(kdb_id)["address"]
        graphrag_input_dir_path = ad + "/db_files/output/latest/artifacts"
    else:
        return {"is_show":False}

    if not entity_josn and not relationship_json:
        return {"is_show":False}
        
    if len(entity_josn) == 0 and len(relationship_json) == 0:
        return {"is_show":False}

    if not relationship_json:
        relationship_source_name = {}
        relationship_target_name = {}
        ef_relationship_id = []
    else:
        if len(relationship_json) == 0:
            relationship_source_name = {}
            relationship_target_name = {}
            ef_relationship_id = []
        else:
            relationship_list = []
            for i in relationship_json:
                relationship_list.append(int(i["id"]))

            # human_readable_id	source	target	description	weight	combined_degree

             # 假设 GRAPHRAG_FOLDER 已定义并指向正确的目录
            rel_df = pd.read_parquet(f'{graphrag_input_dir_path}/create_final_relationships.parquet',
                                    columns=["source","target","human_readable_id"])

            relationship = rel_df.loc[rel_df['human_readable_id'].isin([i for i in relationship_list])]
            relationship_dict = relationship.to_dict()
            relationship_dict = convert_keys_to_int(relationship_dict)
            relationship_list = list(relationship_dict.get("source").keys())

            
            relationship_source_name = relationship_dict.get("source")
            relationship_target_name = relationship_dict.get("target")

            relationship_id = list(relationship_dict.get("source").keys())

            ef_relationship_id = [{"id": i} for i in relationship_id]


    if not entity_josn:
        entity_name = {}
        ef_entity_id = []
    else:
        if len(entity_josn) == 0:
            entity_name = {}
            ef_entity_id = []
        else:
            entity_list = []
            for i in entity_josn:
                entity_list.append(int(i["id"]))

            #读取实体
            # human_readable_id	title type description

            entity_df = pd.read_parquet(f'{graphrag_input_dir_path}/create_final_entities.parquet', 
                                        columns=["title","human_readable_id"])

            # 提取唯一的 type 值并创建类型到类别的映射
            entities = entity_df.loc[entity_df['human_readable_id'].isin(entity_list)]

            entities_dict = entities.to_dict()
            entities_dict = convert_keys_to_int(entities_dict)
            entity_list = list(entities_dict.get("title").keys())

            entity_name = entities_dict.get("title")

            entity_id = list(entities_dict.get("title").keys())

            #{"id": 90}
            ef_entity_id = [{"id": i} for i in entity_id]

    new_id_json = {
                "entity": ef_entity_id,
                "relationship": ef_relationship_id
            }
    print("实体信息:",new_id_json)
    print("实体信息:",entity_name)

    print("实体信息:",relationship_source_name)

    print("实体信息:",relationship_target_name)

    return {"ef_id": new_id_json, "entity_name": entity_name, "relationship_source_name": relationship_source_name, "relationship_target_name":relationship_target_name}
