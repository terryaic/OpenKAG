from typing import Optional, List

from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr
Base = declarative_base()

class User(Base):
    __tablename__ = "users"  # 数据库表名为 'users'

    # 使用 email 作为主键
    email = Column(String, primary_key=True, unique=True, index=True, nullable=False)
    # 存储哈希后的密码
    hashed_password = Column(String, nullable=False)
    # 标志用户是否被禁用
    disabled = Column(Boolean, default=False)
    username = Column(String, unique=True, nullable=True)
    full_name = Column(String)
    role = Column(String, default='user')

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str  # 添加确认密码字段
    username: Optional[str] = None
    full_name: Optional[str] = None
    role:Optional[str] = 'user'
class EmailSchema(BaseModel):
    email: str
class ResetPasswordSchema(BaseModel):
    email: EmailStr
    new_password: str
    confirm_password: str
    verification_code: str
class DeleteUserRequest(BaseModel):
    email: str
class UpdateUserRoleRequest(BaseModel):
    email: str
    new_role: str
class SearchUserRequest(BaseModel):
    search_query: str