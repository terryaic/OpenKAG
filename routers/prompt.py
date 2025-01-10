from datetime import datetime
from fastapi.responses import FileResponse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pathlib import Path
import uuid
from pydantic import BaseModel, FilePath
from typing import Optional
# routers/graphrag.py
from fastapi import APIRouter
import os
from settings import DEFAULT_SETTINGS_PATH
from starlette.templating import Jinja2Templates
from fastapi import Request, UploadFile, File, Form, Query, Body
import shutil
from fileprocesspipeline import FileProcessPipeline
from settings import USING_LLAMAINDEX, USING_LANGCHAIN, USING_RAG
import advancerag
import json
from db import user_kdb_mgdb,file_db, user_kdb_info, share_info, user_prompt_info
from kdbmanager import kdbm
from fastapi.responses import FileResponse
from .graphrag import get_user_path
from apis.version1.route_login import get_resource
from .kdb import get_permissions
from auth.check_login import check_login


templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()


@router.get("/showPrompt", include_in_schema=False)
async def show_kdb(request: Request):
    return check_login(request) or \
    templates.TemplateResponse("prompt/showPrompt.html", {"request": request, "resources": get_resource(request, "showPrompt")})


@router.get("/toCreateNewPrompt", include_in_schema=False)
async def create_kdb(request: Request):
    return check_login(request) or \
    templates.TemplateResponse("prompt/create_prompt.html", {"request": request, "value": "新建的提示词", "share": False, 
                                                                "permissions": get_permissions(request), "resources": get_resource(request, "create_prompt")})


@router.get("/toPrompt", include_in_schema=False)
async def create_kdb(request: Request, title: str, share_type: bool, is_from_share: bool):
    return check_login(request) or \
    templates.TemplateResponse("prompt/create_prompt.html", {"request": request, "value": title, "share": share_type, "is_from_share": is_from_share, 
                                                                "permissions": get_permissions(request), "resources": get_resource(request, "create_prompt")})


@router.get("/backShowPrompt", include_in_schema=False)
async def backShowKdb(request: Request):
    return check_login(request) or \
    templates.TemplateResponse("prompt/showPrompt.html", {"request": request, "resources": get_resource(request, "showPrompt")})


@router.post("/get_user_prompt")
async def get_kdb(request:Request):
    import json

    user_id = request.cookies.get("current_user")
    if not user_id:
        return None
    else:
        user_prompt = user_prompt_info.get_user_prompt(user_id)
        data = []

        if user_prompt:
            # 用户存在数据库中
            data = user_prompt
        else:
            # 不存在数据库中
            print("用户没有数据")
            

        return {"user_info":data}
    

@router.post("/get_share_prompt")
async def get_kdb(request:Request):
    import json

    user_id = request.cookies.get("current_user")
    if not user_id:
        return None
    else:
        share_prompt = user_prompt_info.get_share_prompt()
        data = []

        if share_prompt:
            # 用户存在数据库中
            data = share_prompt
        else:
            # 不存在数据库中
            print("用户没有数据")
            

        return {"share_info":data}
    

@router.post("/change_prompt_title")
async def change_kdb_title(request: Request):
    body = await request.json()  # 解析请求体
    old_title = body.get('old_title')  # 获取 old_title
    new_title = body.get('new_title')  # 获取 new_title
    prompt = body.get('prompt')  # 获取 new_title
    user_id = request.cookies.get("current_user")
    if not user_id:
        return {"is_change": False}
    else:
        # 添加一个prompt信息
        # user_prompt_info.add_user_prompt(user_id, "test", False, "2004", "test prompt")
        # 判读是否是唯一的title
        if_new_title_exists = user_prompt_info.if_title_exists(new_title)
        if if_new_title_exists:
            return {"is_change": False, "message": "名字以存在，请修改名字！"}
        
        if_old_title_exists = user_prompt_info.if_title_exists(old_title)

        if not if_old_title_exists:
            formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_prompt_info.add_user_prompt(user_id, new_title, False, str(formatted_time), prompt)
            return {"is_add": True}
        
        user_prompt_info.change_prompt_title(old_title, new_title)
        return {"is_change": True}
    


@router.post("/change_user_prompt_share")
async def change_kdb_share(request: Request):
    body = await request.json()  # 解析请求体
    title = body.get('title')  # 获取 old_title
    share_type = body.get('share_type')  # 获取 new_title
    user_id = request.cookies.get("current_user")

    if not user_id:
        return {"is_change": False}
    else:
        if not user_prompt_info.if_title_exists(title):
            return {"is_change": False}
        user_prompt_info.change_prompt_share_type(title, share_type)
        return {"is_change": True}
    

@router.post("/change_user_prompt_content")
async def change_user_prompt_content(request: Request):
    body = await request.json()  # 解析请求体
    title = body.get('title')  # 获取 old_title
    content = body.get('prompt')  # 获取 new_title
    user_id = request.cookies.get("current_user")

    if not user_id:
        return {"is_change": False}
    else:
        if not user_prompt_info.if_title_exists(title):
            return {"is_change": False}
        user_prompt_info.change_prompt_content(title, content)
        return {"is_change": True}
    

@router.post("/get_user_prompt_content")
async def get_user_prompt_content(request: Request):
    body = await request.json()  # 解析请求体
    title = body.get('title')  # 获取 old_title
    user_id = request.cookies.get("current_user")

    if not user_id:
        return {"content": False}
    else:
        if not user_prompt_info.if_title_exists(title):
            return {"error": True}
        content = user_prompt_info.get_prompt_content(title)
        return {"content": content}
    

@router.post("/delete_prompt")
async def delete_prompt(request: Request):
    body = await request.json()  # 解析请求体
    title = body.get('title')  # 获取 old_title

    # 删除文件夹
    import shutil
    import os

    try:
        result = user_prompt_info.delete_prompt(title)
        return {"is_delete": True}

    except Exception as e:
        return {"error": f"未知错误: {str(e)}"}
    

@router.post("/get_share_user_prompt")
async def get_share_user_prompt(request:Request):
    import json

    all_prompt = {"user":[],"share":[]}

    user_id = request.cookies.get("current_user")

    if not user_id:
        return None

    else:
        user_prompt = user_prompt_info.get_user_prompt(user_id)
        all_prompt["user"] = user_prompt

        share_prompt = user_prompt_info.get_share_prompt()

        all_prompt["share"] = share_prompt

        print("prompt", all_prompt)
        return all_prompt
    

