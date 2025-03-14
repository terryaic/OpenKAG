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
        # 创建数据库表
        await conn.run_sync(Base.metadata.create_all)

    # 添加匿名用户
    async with AsyncSessionLocal() as session:  # 获取会话
        stmt = select(User).where(User.email == "anonymous_user")
        result = await session.execute(stmt)
        user_exists = result.scalar_one_or_none()  # 检查匿名用户是否存在

        if not user_exists:
            # 向数据库添加匿名用户
            user = User(
                email="anonymous_user",
                hashed_password="",
                username="",
                full_name="",
                disabled=False,
                role="anonymous_user"  # 默认角色
            )
            session.add(user)  # 添加到会话
            await session.commit()  # 提交会话
            await session.refresh(user)  # 刷新以获取 ID 等信息

# 获取异步数据库会话
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_db)):
    yield SQLAlchemyUserDatabase(session, User)