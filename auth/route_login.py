# -*- coding: UTF-8 -*-
#from apis.version1.route_login import login_for_access_token
#from db.session import get_db

import time
import random
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request, Response
from fastapi.templating import Jinja2Templates
#from sqlalchemy.orm import Session
from auth.forms import LoginForm
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import RedirectResponse
#from rag.apis.version1.route_login import pwd_context
from fastapi.responses import JSONResponse
from .models import User, UserCreate,EmailSchema,ResetPasswordSchema,DeleteUserRequest,UpdateUserRoleRequest,SearchUserRequest# 确保导入 User 模型
from .session import get_async_db, init_db  # 确保导入异步数据库会话
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from aiosmtplib.errors import SMTPResponseException
from apis.version1.route_login import login_for_access_token,authenticate_user,get_current_user
from settings import MAIL_USERNAME,MAIL_PASSWORD,MAIL_FROM,MAIL_PORT,MAIL_SERVER,MAIL_STARTTLS,MAIL_SSL_TLS,USE_CREDENTIALS
from apis.version1.route_login import get_resource
from fastapi import HTTPException, status
from db import session_mgr, modb_api
from auth.check_login import check_login

#from fastapi_login.exceptions import InvalidCredentialsException
#from fastapi_login import LoginManager
# 邮件配置（谁发的）
# 连接配置

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,  # 显示的名字
    MAIL_PASSWORD=MAIL_PASSWORD,  # 邮箱密码
    MAIL_FROM=MAIL_FROM,  # 实际邮箱账号
    MAIL_PORT=MAIL_PORT,  # SSL端口
    MAIL_SERVER= MAIL_SERVER ,# QQ SMTP服务器
    MAIL_STARTTLS=MAIL_STARTTLS,  # 不使用 STARTTLS
    MAIL_SSL_TLS=MAIL_SSL_TLS,  # 使用 SSL/TLS
    USE_CREDENTIALS=USE_CREDENTIALS,  # 使用凭据
)
print("MAIL_PASSWORD:","aiihfiznkyfvceci")
print(type(MAIL_PASSWORD))
print("MAIL_FROM:",MAIL_FROM)
print(type(MAIL_FROM))
print("MAIL_PORT:",MAIL_PORT)
print(type(MAIL_PORT))
print("MAIL_SSL_TLS:",MAIL_SSL_TLS)
print(type(MAIL_SSL_TLS))
print("MAIL_SSL_TLS:",MAIL_SSL_TLS)
print(type(MAIL_SSL_TLS))
print("USE_CREDENTIALS:",USE_CREDENTIALS)
print(type(USE_CREDENTIALS))


#manager = LoginManager(SECRET, token_url='/auth/token')

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")
router = APIRouter(include_in_schema=False)


@router.get("/login")
def login(request: Request):
    error_message = request.headers.get("X-Error-Message", None)
    return templates.TemplateResponse("auth/login.html", {"request": request,"error_message": error_message, "resources": get_resource(request, "login")})


@router.post("/login")
async def login(request: Request ,session: AsyncSession = Depends(get_async_db)):
    form = LoginForm(request)
    await form.load_data()

    # 如果表单无效，返回带有错误信息的模板
    if not await form.is_valid():
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "form": form,
                "error_message": "Incorrect email or password.",  # 错误信息
                "resources": get_resource(request, "login")
            }
        )

    # 如果表单有效，尝试认证用户
    try:
        email = form.username
        password = form.password
        user = await authenticate_user(session, email, password)
        if user:
            # 登录成功后返回到首页或其他页面
            response = templates.TemplateResponse(
                "/index.html",
                {"request": request, "form": form, "current_user": email, "mode": "chat",
                 "resources": get_resource(request, "index")}
            )
            await login_for_access_token(request=request, response=response, form_data=form, db=session)
            return response

    except HTTPException as e:
        # 如果认证失败，返回错误信息
        form.errors.append(str(e.detail))  # 将认证失败的错误信息加入错误列表
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "form": form,
                "error_message": "Incorrect email or password.",  # 错误信息
                "resources": get_resource(request, "login")
            }
        )

#async def login(request: Request, db: Session = Depends(get_db)):
# async def login(request: Request):
#     form = LoginForm(request)
#     await form.load_data()
#     if await form.is_valid():
#         try:
#             """
#             user = load_user(form.username)  # we are using the same function to retrieve the user
#             if not user:
#                 raise InvalidCredentialsException  # you can also use your own HTTPException
#             elif form.password != user['password']:
#                 raise InvalidCredentialsException
#             """
#             form.__dict__.update(msg="Login Successful :)")
#             response = templates.TemplateResponse("index.html",  {"request": request})
#
#             login_for_access_token(response=response, form_data=form, db=fake_users_db)
#             return response
#         except HTTPException:
#             form.__dict__.update(msg="")
#             form.__dict__.get("errors").append("Incorrect Email or Password")
#             return templates.TemplateResponse("auth/login.html", form.__dict__)
#     return templates.TemplateResponse("auth/login.html", form.__dict__)


#new_password123
# 设置日志配置
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@router.post("/register")
async def register(
    user_create: UserCreate,
    session: AsyncSession = Depends(get_async_db)
):
    await init_db()
    logger.info("开始注册")
    print("正在注册")
    # 检查用户输入
    if not user_create.email or not user_create.password:
        raise HTTPException(status_code=400, detail="Email and password cannot be empty")
    if user_create.password != user_create.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    # 检查电子邮件是否已存在
    result = await session.execute(select(User).where(User.email == user_create.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    result = await session.execute(select(User))
    existing_users = result.scalars().all()
    if not existing_users:
        user_role = 'admin'
    else:
        user_role = 'user'
    # 创建新用户
    hashed_password = pwd_context.hash(user_create.password)
    user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        username=user_create.username,
        full_name=user_create.full_name,
        disabled=False ,
        role=user_role # 默认不禁用
    )

    session.add(user)  # 将用户添加到会话
    await session.commit()  # 提交会话
    await session.refresh(user)  # 刷新以获取新用户的 ID 等信息
    logger.info("用户注册成功: %s", user.email)
    return RedirectResponse(url="/login", status_code=303)
verification_codes = {'2114726656@qq.com': (123456, 1729483306.5397518)}
CODE_EXPIRY_TIME = 30 * 60
def generate_random_number():
    return random.randint(100000, 999999)

@router.post("/send_verification_code")
async def send_verification_code(email: EmailSchema):
    if not email:
        raise HTTPException(status_code=400, detail="邮箱不能为空")
    if email.email in verification_codes:
        del verification_codes[email.email]
    code=generate_random_number()
    template = f"""
    <html>
    <body>
        <p>Hi !!!</p>
        <p>Thanks for haifeng ai , your code is {code}!!!</p>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=[email.email],
        body=template,
        subtype="html"
    )
    fm = FastMail(conf)
        # 异步发送邮件
    verification_codes[email.email] = (code, time.time())
    print(verification_codes)
    try:
        # 异步发送邮件
        await fm.send_message(message)
    except SMTPResponseException as e:
        # 捕获SMTP异常并记录日志（如有需要），同时返回成功
        if e.code == -1:
            print(f"捕获到 SMTPResponseException: {e}, 认为发送成功")
            return {"success": True, "message": "验证码已发送!"}
        else:
            raise HTTPException(status_code=500, detail=f"邮件发送失败: {e}")

    return {"success": True, "message": "验证码已发送!"}


#{"detail":[{"type":"missing","loc":["query","email"],"msg":"Field required","input":null},{"type":"missing","loc":["query","new_password"],"msg":"Field required","input":null},{"type":"missing","loc":["query","confirm_password"],"msg":"Field required","input":null},{"type":"missing","loc":["query","verification_code"],"msg":"Field required","input":null}]}


@router.post("/reset_password")
async def reset_password(
    request: Request,
    reset_password_data: ResetPasswordSchema,  # 使用 Pydantic 模型
    session: AsyncSession = Depends(get_async_db),

):
    email = reset_password_data.email
    new_password = reset_password_data.new_password
    confirm_password = reset_password_data.confirm_password
    verification_code = reset_password_data.verification_code
    print(email)
    print(new_password)
    print(confirm_password)
    print("verification_code1",verification_code)
    # 验证验证码
    print("verification_code2",verification_codes[email][0])
    print(str(verification_codes[email][0]) != str(verification_code))
    print( email not in verification_codes)

    if email not in verification_codes or str(verification_codes[email][0]) != str(verification_code):
        raise HTTPException(status_code=400, detail="无效的验证码")
    startime=verification_codes[email][1]
    if time.time() - startime > CODE_EXPIRY_TIME:
        del verification_codes[email]
        raise HTTPException(status_code=404, detail="验证码已超时")
    # 确认新密码和确认密码匹配
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="新密码和确认密码不匹配")

    # 查询用户
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # 哈希新密码并更新
    user.hashed_password = pwd_context.hash(new_password)

    await session.commit()  # 提交更改
    #await session.refresh(user)  # 刷新用户数据

    # 清空验证码
    del verification_codes[email]
    print("重置密码完成")
    return  RedirectResponse(url="/login", status_code=303)
@router.post("/get_user")
def get_current_user_fetch(request: Request):
    return get_current_user(request)
#网易：LZRirCw5ma8LTNuz，qq：aiihfiznkyfvceci
@router.post("/enterAdmin")
async def checkAdmin(request: Request,db: AsyncSession = Depends(get_async_db)):
    user_id = request.cookies.get("current_user")
    if not user_id:
        raise HTTPException(status_code=400, detail="用户未登录")
        # 查询数据库中的用户
    async with db.begin():
        result = await db.execute(select(User).filter_by(email=user_id))  # 假设 user_id 是 email 字段
        user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")
        # 获取用户的角色
    role = user.role
    # 根据角色决定是否有权限访问管理员界面
    if role != "admin":
        raise HTTPException(status_code=403, detail="没有权限访问管理员界面")
    # 如果用户是管理员，返回成功
    return RedirectResponse(url="/admin",status_code=303)
@router.get("/admin")
async def admin_dashboard(request: Request):
    return  check_login(request) or \
    templates.TemplateResponse("auth/admin.html", {"request": request, "resources": get_resource(request, "admin")})

@router.post("/admin2user")
async def admin2user(request: Request, db: AsyncSession = Depends(get_async_db)):
    # 从请求中获取当前用户的 email
    current_user_email = request.cookies.get("current_user")
    if not current_user_email:
        raise HTTPException(status_code=400, detail="用户未登录")
    # 查询所有用户的 email 和 role，排除当前用户
    async with db.begin():
        result = await db.execute(select(User.email, User.role).filter(User.email != current_user_email))
        users = result.fetchall()  # 获取查询结果
    # 将查询结果转化为列表格式
    user_list = [{"email": user.email, "role": user.role} for user in users]
    return user_list


@router.post("/deleteUser")
async def delete_user(request: Request, data: DeleteUserRequest, db: AsyncSession = Depends(get_async_db)):
    # 从请求体中获取 email
    email = data.email

    # 获取当前登录用户的 email
    current_user_email = request.cookies.get("current_user")
    if not current_user_email:
        raise HTTPException(status_code=400, detail="用户未登录")

    # 查询当前用户是否为管理员
    async with db.begin():
        result = await db.execute(select(User).filter_by(email=current_user_email))
        current_user = result.scalars().first()

    if not current_user:
        raise HTTPException(status_code=404, detail="用户未找到")

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="没有权限删除用户")

    # 查询要删除的用户
    async with db.begin():
        result = await db.execute(select(User).filter_by(email=email))
        user_to_delete = result.scalars().first()

    if not user_to_delete:
        raise HTTPException(status_code=404, detail="要删除的用户不存在")

    # 删除用户
    async with db.begin():
        await db.delete(user_to_delete)
        await db.commit()
    return JSONResponse(content={"message": f"用户 {email} 删除成功"}, status_code=200)

@router.post("/updateUserRole")
async def update_user_role(
        request: Request,
        data: UpdateUserRoleRequest,
        db: AsyncSession = Depends(get_async_db)
):
    # 从请求体中获取 email 和新角色
    email = data.email
    new_role = data.new_role

    # 获取当前登录用户的 email
    current_user_email = request.cookies.get("current_user")
    if not current_user_email:
        raise HTTPException(status_code=400, detail="用户未登录")

    # 查询当前用户是否为管理员
    async with db.begin():
        result = await db.execute(select(User).filter_by(email=current_user_email))
        current_user = result.scalars().first()

    if not current_user:
        raise HTTPException(status_code=404, detail="用户未找到")

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="没有权限修改用户角色")

    # 查询需要修改角色的用户
    result = await db.execute(select(User).filter_by(email=email))
    user_to_update = result.scalars().first()

    if not user_to_update:
        raise HTTPException(status_code=404, detail="要修改的用户不存在")

    # 修改用户角色
    user_to_update.role = new_role
    await db.commit()

    return JSONResponse(content={"message": f"用户 {email} 的角色已修改为 {new_role}"}, status_code=200)
    #return RedirectResponse(url="/admin",status_code=303)


@router.post("/searchUserByEmail")
async def search_user_by_email(request: Request, search_request: SearchUserRequest, db: AsyncSession = Depends(get_async_db)):
    # 从请求中获取当前用户的 email
    current_user_email = request.cookies.get("current_user")
    if not current_user_email:
        raise HTTPException(status_code=400, detail="用户未登录")
    search_query = search_request.search_query
    # 确保搜索查询字符串不为空
    if not search_query:
        raise HTTPException(status_code=400, detail="搜索查询不能为空")

    # 查询所有用户的 email 和 role，排除当前用户，并且email包含搜索关键字F
    async with db.begin():
        result = await db.execute(
            select(User.email, User.role)
            .filter(User.email != current_user_email)
            .filter(User.email.ilike(f"%{search_query}%"))  # 使用 ilike 实现不区分大小写的匹配
        )
        users = result.fetchall()  # 获取查询结果

    # 将查询结果转化为列表格式
    user_list = [{"email": user.email, "role": user.role} for user in users]

    # 返回匹配的用户信息
    return user_list


@router.post("/get_current_language")
async def get_current_language(request: Request):
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
    return {"language": language or "en"}  # 默认返回英文


@router.post("/change_language")
async def change_language(request: Request, response: Response):
    """
    改变当前语言并存储在 Cookies 中。

    Args:
        request (Request): 请求对象。
        response (Response): 响应对象。

    Returns:
        dict: 包含成功设置的语言信息。
    """
    # 从请求体中获取 JSON 数据
    body = await request.json()
    language = body.get("language")

    if not language:
        return {"error": "Language is required"}

    # 打印传入的语言参数
    print("设置的新语言:", language)

    # 设置 Cookies
    response.set_cookie(key="current_language", value=language, httponly=True)

    # 返回确认信息
    return {"message": "Language changed successfully", "language": language}


@router.post("/delete_history")
async def delete_history(request: Request):
    body = await request.json()  # 解析请求体
    session = body.get('session')  # 获取 old_title
    result = session_mgr.delete_session(session)
    print("=====时候成功删除历史记录：",result)
    if result:    
        # 返回确认信息
        result_history = await modb_api.delete_session_data(session)
        if result_history:
            return {"is_delete":True}
    return {"is_delete":False}
