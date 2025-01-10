import jwt
from jwt import ExpiredSignatureError
from authsettings import *
from starlette.responses import RedirectResponse


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
        print("expired")
        return False
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

def check_login(request):
    if not login_required(request):
        response = RedirectResponse(url="/login",status_code=303)
        return response
    else:
        return None