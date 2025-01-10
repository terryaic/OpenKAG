import os

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from settings import SQL_DB_PATH_2USERS
# 动态获取项目根目录
current_directory = os.getcwd()
db_path = os.path.join(current_directory, SQL_DB_PATH_2USERS)
print("db_path",db_path)
db_url = f"sqlite+aiosqlite:///{db_path}"
# 确保数据库目录存在
from .models import Base,User

# 创建异步引擎
async_engine = create_async_engine(db_url, echo=True)

# 创建异步会话
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

from sqlalchemy.future import select
# 创建数据库表（异步）
async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



# 获取异步数据库会话
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
async def get_user_db(session: AsyncSession = Depends(get_async_db)):
    yield SQLAlchemyUserDatabase(session, User)