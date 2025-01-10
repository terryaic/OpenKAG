import logging
import sys

from settings import DEBUG
if DEBUG:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

from fastapi import FastAPI, File, Form, Body, Header,Depends
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

from apis.version1.route_login import get_current_user, get_resource

app = FastAPI(title='Knowledge is better',description='',version='1.0')

from fastapi import APIRouter
from auth import route_login
import web
from routers import graphrag, kdb, spider, prompt
from db import session_mgr
from db.modb_api import get_context_sessionid
from auth.check_login import check_login


api_router = APIRouter()
api_router.include_router(route_login.router, prefix="", tags=["auth-webapp"])
api_router.include_router(web.router, prefix="", tags=["webapp"])
api_router.include_router(graphrag.router, prefix="/graphrag", tags=["graphrag"])
api_router.include_router(kdb.router, prefix="/kdb", tags=["kdb"])
api_router.include_router(spider.router, prefix="/spider", tags=["spider"])
api_router.include_router(prompt.router, prefix="/prompt", tags=["prompt"])
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

@app.get("/", include_in_schema=False)
async def index(request: Request, prompt_name=""):
    return  check_login(request) or \
    templates.TemplateResponse("index.html",  {"request": request, "mode": "chat", "prompt_name": prompt_name, "resources": get_resource(request, "index")})

@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request,"resources":get_resource(request, "register")})


@app.get("/chatbox/{session_id}", include_in_schema=False)
async def chatbox(request: Request, session_id:str, mode: str="chat", kdb_id: str="", prompt_name=""):
    user = request.cookies.get("current_user")
    response = check_login(request)
    if response:
        return response
    session = session_mgr.get_session(session_id)
    if session:
        if session['update_time'] == session['create_time']:
            text_to_send = session['title']
            session_mgr.update_session(session)
            return templates.TemplateResponse("chatbox.html",  {"request": request,"user": user, "session_id": session_id, "text_to_send": text_to_send, "history_list":[], "mode": mode, "kdb_id": kdb_id, "prompt_name": prompt_name,"resources": get_resource(request, "chatbox")})

    history_list=await get_context_sessionid(session_id)
    return templates.TemplateResponse("chatbox.html",  {"request": request,"user": user, "session_id": session_id,"history_list":history_list, "mode": mode, "kdb_id": kdb_id, "prompt_name": prompt_name,"resources": get_resource(request, "chatbox")})

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
    user = request.cookies.get("current_user")
    kb_id = request.cookies.get("kb_id")
    body = await request.json()  # 解析请求体
    message = body.get('message')  # 获取 old_title
    session_id = uuid.uuid4().hex
    body = await request.json()
    message = body.get('message')
    print("message:",message)
    if message:
        print("保存历史记录")
        session_mgr.create_session(user, session_id, message,kb_id)
    return {"session_id": session_id}

@app.get("/conversation/list", include_in_schema=False)
async def conversation_list(request: Request):
    user = request.cookies.get("current_user")
    conversations = session_mgr.list_session(user)
    ret = []
    for conv in conversations:
        ret.append({"id": conv['session_id'], "title": conv['title'] if 'title' in conv.keys() else 'empty'})
    return {"conversations": ret}
#知识库跳转到index
@app.get("/index/{session_id}", include_in_schema=False)
async def jumpToindex(request: Request,mode: str="chat", kdb_id: str="", prompt_name=""):
    return  check_login(request) or \
    templates.TemplateResponse("index.html",  {"request": request, "mode": mode,"kdb_id":kdb_id,"prompt_name": prompt_name,"resources": get_resource(request, "index")})
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
