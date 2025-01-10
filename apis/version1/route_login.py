# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta
import jwt
from fastapi import Depends, FastAPI, HTTPException, Response
from starlette import status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext  # passlib 处理哈希加密的包
from pydantic import BaseModel
from apis.utils import OAuth2PasswordBearerWithCookie    #new
from authsettings import *
from fastapi import APIRouter
from auth.models import Base,User
from fastapi import Request
import os
import json
from db.modb_api import get_context_sessionid
import locale
from authsettings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from db import user_db

router = APIRouter(include_in_schema=False)


'''FastAPI参数类型验证模型'''
# token url相应模型
class Token(BaseModel):
    access_token: str
    token_type: str

# 令牌数据模型
class TokenData(BaseModel):
    username: str = None



pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# verify_password验证密码
# plain_password普通密码, hashed_password哈希密码
# 返回True和False
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 获取哈希密码;普通密码进去，对应的哈希密码出来。
def get_password_hash(password):
    return pwd_context.hash(password)
from sqlalchemy.future import select
# 数据库读取用户信息
async def get_user(db, email: str):
    print("emailemailemailemailemail", email)
    print("emailemailemailemailemail", email)
    stmt = select(User).where(User.email == email)  # Assuming you have a User model
    result = await db.execute(stmt)  # Execute the query
    user = result.scalars().first()  # Get the first result

    if user:
        print("user_dictuser_dictuser_dict", user)
        return user
    else:
        return None

# 验证用户
async def authenticate_user(db, email: str, password: str):
    print("校验中")
    user = await get_user(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# 创建访问令牌（token）
def create_access_token(*, data: dict, expires_delta: timedelta = None):
    print("正在创建令牌")
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta  # expire 令牌到期时间
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print("令牌创建完成")
    return encoded_jwt

@router.post("/token", response_model=Token)
async def login_for_access_token(request: Request, response: Response,form_data: OAuth2PasswordRequestForm = Depends(), db=None):  #added response as a function parameter
    user =await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    print("正在设置token")
    response.set_cookie(key="access_token",value=f"Bearer {access_token}", httponly=True)  #set HttpOnly cookie in response
    print("access_token")
    response.set_cookie(key="current_user", value=user.email, httponly=True)

    print("current_user")
    print("token设置完成")
    return {"access_token": access_token, "token_type": "bearer"}

#备选方案，fetch的方法获取历史记录，request的方法不可行时使用
@router.post("/send_data")
async  def senddata(session_id):
    history_list = await get_context_sessionid(session_id)
    return history_list

def get_current_user(request: Request):
    current_user = request.cookies.get("current_user")
    return current_user

def get_user_role(request: Request):
    user_id = request.cookies.get("current_user")
    user_role = user_db.get_user_role(user_id)
    print("用户的角色是：",user_role)
    return user_role

def get_resource(request: Request, page_name):
    language = request.cookies.get("current_language")
    if not language:
        # 从请求头中提取 'Accept-Language'
        accept_language = request.headers.get("accept-language")
        if accept_language:
            # 解析 'Accept-Language' 获取首选语言
            language = [lang.split(";")[0].strip() for lang in accept_language.split(",")][0]
        print("当前的语言:",language)
    file_name = page_name + ".json"    
    if language == "zh" or language == "zh-CN" or language == "zh-TW" or language == "zh-HK":
        file_path = os.path.join("resources","zh",file_name)
    else:
        file_path = os.path.join("resources","en",file_name)

    # 打开并读取 JSON 文件
    with open(file_path, 'r', encoding='utf-8') as file:
        source = json.load(file)

    return source
