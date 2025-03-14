import logging
import sys

from settings import DEBUG,AVATAR_ENABLED
if DEBUG:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
from fastapi import HTTPException, status
from fastapi import FastAPI, File, Form, Body, Header, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging
from typing import Any
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.responses import RedirectResponse
import uuid
from authsettings import *
from fastapi import Response

from apis.version1.route_login import get_current_user, get_resource, create_access_token

app = FastAPI(title='Knowledge is better',description='',version='1.0')

from fastapi import APIRouter
from auth import route_login
import web
from routers import graphrag, kdb, spider, prompt
from db import session_mgr,session_file_db,modb_api
from db.modb_api import get_context_sessionid
from auth.check_login import check_login

from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from datetime import datetime, timedelta
class TokenRefreshMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print("检测到有更新，token已更新")
        response = await call_next(request)
        # 检查 Cookie 中是否有 Token
        token = request.cookies.get("access_token")
        if token:
            try:
                # 解码 Token
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                exp = payload.get("exp")

                if not username or not exp:
                    return response  # 跳过刷新

                # 检查是否需要刷新 Token
                now = datetime.utcnow()
                token_expiry = datetime.utcfromtimestamp(exp)
                if token_expiry - now < timedelta(minutes=60):  # 快过期时刷新
                    new_token = create_access_token(
                        data={"sub": username},
                        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                    )
                    response.set_cookie(key="access_token", value=f"Bearer {new_token}", httponly=True)
            except Exception as e:
                # 如果 Token 无效，继续原始响应
                pass
        return response


# FastAPI 实例
app = FastAPI()

# 添加中间件
app.add_middleware(TokenRefreshMiddleware)

api_router = APIRouter()
api_router.include_router(route_login.router, prefix="", tags=["auth-webapp"])
api_router.include_router(web.router, prefix="", tags=["webapp"])
api_router.include_router(graphrag.router, prefix="/graphrag", tags=["graphrag"])
api_router.include_router(kdb.router, prefix="/kdb", tags=["kdb"])
api_router.include_router(spider.router, prefix="/spider", tags=["spider"])
api_router.include_router(prompt.router, prefix="/prompt", tags=["prompt"])

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
if AVATAR_ENABLED:
    from avatar import main as avatar_main
    api_router.include_router(avatar_main.router, prefix="", tags=["avatar"])
    sub_static_dir = BASE_DIR / "avatar" / "static"
    app.mount("/avatar-static", StaticFiles(directory=str(sub_static_dir)), name="avatar-static")
    
app.include_router(api_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/check-token")
async def check_token(request: Request):
    # 检查 Cookie 中是否存在 access_token
    print("fetching check token")
    await check_login(request)
    return {"message": "Token is present and valid"}
@app.get("/", include_in_schema=False)
async def index(request: Request, prompt_name=""):
    return  await check_login(request) or \
    templates.TemplateResponse("index.html",  {"request": request, "mode": "chat", "prompt_name": prompt_name, 
                                               "resources": get_resource(request, "index"),
                                               "permissions": kdb.get_permissions(request)})

@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request,"resources":get_resource(request, "register")})


@app.get("/chatbox/{session_id}", include_in_schema=False)
async def chatbox(request: Request, session_id:str, mode: str="chat", kdb_id: str="", prompt_name=""):
    import json
    user = request.cookies.get("current_user")
    response = await check_login(request)
    if response:
        return response
    session = session_mgr.get_session(session_id)
    print("session-------:",session)
    # index->chatbox
    if session:
        if session['update_time'] == session['create_time']:
            text_to_send = session['title']
            session_mgr.update_session(session)
            file_to_send = await modb_api.get_file_record(session_id)
            file_to_send = file_to_send or "[]"
            return templates.TemplateResponse("chatbox.html",  {"request": request,"user": user, "session_id": session_id, "text_to_send": text_to_send, 
                                                                "file_to_send": file_to_send,"history_list":[], "mode": mode, "kdb_id": kdb_id, 
                                                                "prompt_name": prompt_name,"resources": get_resource(request, "chatbox"),
                                                                "permissions": kdb.get_permissions(request)
                                                                })
    #index->chatbox
    history_list=await get_context_sessionid(session_id)
    return templates.TemplateResponse("chatbox.html",  {"request": request,"user": user, "session_id": session_id,"history_list":history_list, 
                                                        "mode": mode, "kdb_id": kdb_id, "prompt_name": prompt_name,
                                                        "resources": get_resource(request, "chatbox"),
                                                        "permissions": kdb.get_permissions(request)
                                                        })

@app.get("/minichatbox/{session_id}", include_in_schema=False)
async def chatbox(request: Request, session_id:str, mode: str="faq", kdb_id: str="", prompt_name=""):
    import json
    user = request.cookies.get("current_user")
    #index->chatbox
    history_list=await get_context_sessionid(session_id)
    return templates.TemplateResponse("mini_chatbox.html",  {"request": request,"user": user, "session_id": session_id,"history_list":history_list, 
                                                        "mode": mode, "kdb_id": kdb_id, "prompt_name": prompt_name,
                                                        "resources": get_resource(request, "chatbox")
                                                        })

@app.get("/reset_password")
async def reset_password(request: Request):
    return templates.TemplateResponse("auth/reset_password.html", {"request": request,"resources": get_resource(request, "reset_password")})



@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="current_user")
    response.delete_cookie(key="current_language")

    return {"detail": "Successfully logged out"}

@app.post("/conversation", include_in_schema=False)
async def conversation(request: Request):
    print("request",request)
    user = request.cookies.get("current_user")
    kb_id = request.cookies.get("kb_id")
    body = await request.json()  # 解析请求体
    message = body.get('message')
    create_session_id = body.get("create_session_id")
    session_id = body.get("session_id")
    files = body.get("files")

    if create_session_id:
        session_id = uuid.uuid4().hex
        return {"session_id": session_id}
    if message:
        if not session_id:
            session_id = uuid.uuid4().hex
        if files:
            await modb_api.insert_session_file_upload(files,session_id)
        print("保存历史记录")
        session_mgr.create_session(user, session_id, message,kb_id)
    return {"session_id": session_id}

@app.get("/conversation/list", include_in_schema=False)
async def conversation_list(request: Request):
    user = request.cookies.get("current_user")
    conversations = session_mgr.list_session(user)
    ret = []
    for conv in conversations:
        ret.append({"id": conv['session_id'], "title": conv['title'] if 'title' in conv.keys() else 'empty', "time": web.get_readable_time(conv['create_time'])})
    return {"conversations": ret}
#知识库跳转到index
@app.get("/index/{session_id}", include_in_schema=False)
async def jumpToindex(request: Request,mode: str="chat", kdb_id: str="", prompt_name=""):
    return  await check_login(request) or \
    templates.TemplateResponse("index.html",  {"request": request, "mode": mode,"kdb_id":kdb_id,"prompt_name": prompt_name,
                                               "resources": get_resource(request, "index"),
                                               "permissions": kdb.get_permissions(request)})
#async function fetchCurrentUser() {
#     try {
#         const response = await fetch("http://127.0.0.1:8000/userid", {
#             method: "get",
#             credentials: "same-origin",
#             headers: {
#                 "Content-Type": "application/json"
#             }
#         });
#
#         if (!response.ok) {
#             console.error("请求失败，状态码:", response.status);
#             return;
#         }
#
#         const data = await response.json(); // 获取数据
#         console.log("当前用户:", data.current_user);
#
#         // 在页面上显示当前用户
#         document.getElementById("username").textContent = data.current_user || '未知用户';
#     } catch (error) {
#         console.error("请求失败:", error);
#     }
# }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
