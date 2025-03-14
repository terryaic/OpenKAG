import jwt
from jwt import ExpiredSignatureError
from authsettings import *
from starlette.responses import RedirectResponse
from fastapi.websockets import WebSocket

def judgeToken(token):
    """
    判断token
    :param token: token串
    :return: boolen
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        return True
    except ExpiredSignatureError as e:
        print("expired",e)
        return None
    except Exception as e:
        print("token 验证失败,{}".format(str(e)))
        return False


from fastapi.security.utils import get_authorization_scheme_param


def checkToken(request):
    authorization: str = request.cookies.get("access_token")  # changed to accept access token from httpOnly Cookie

    scheme, param = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer":
        return None  # token格式不正确，返回None

    return param
    # if not authorization or scheme.lower() != "bearer":
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Not authenticated",
    #             headers={"WWW-Authenticate": "Bearer"},
    #         )
    # return param


def login_required(request):
    """
    登录认证token
    :param token:
    :return:boolen
    """
    token = checkToken(request)
    return judgeToken(token)


async def check_disabled(request):
    from auth.session import get_async_db
    from sqlalchemy import text
    # 获取用户 ID
    user_id = request.cookies.get("current_user")

    # 使用 get_async_db 获取数据库会话
    async for db in get_async_db():
        # 查询数据库
        query = text("SELECT disabled FROM users WHERE email = :email")
        result = await db.execute(query, {"email": user_id})
        # 使用 scalars() 提取列值
        disabled = result.scalars().first()

        # 检查用户状态
        if disabled:  # 如果用户被禁用
            return True  # 用户被禁用
        return False  # 用户未被禁用

async def check_login(request):
    """
    检查登录状态并根据请求类型进行处理。
    """
    if await check_disabled(request):
        # 如果是 WebSocket 请求
        if isinstance(request, WebSocket):
            return {"action": "redirect", "url": "/login"}  # 返回重定向指令

        # 如果是普通 HTTP 请求
        return RedirectResponse(url="/login", status_code=303)
    
    if not login_required(request):  # 假设 login_required 函数检查登录状态
        print("未登录，处理重定向")

        # 如果是 WebSocket 请求
        if isinstance(request, WebSocket):
            return {"action": "redirect", "url": "/login"}  # 返回重定向指令

        # 如果是普通 HTTP 请求
        return RedirectResponse(url="/login", status_code=303)
    else:
        return None