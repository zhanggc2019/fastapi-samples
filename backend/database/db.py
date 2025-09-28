#!/usr/bin/env python3
import sys
from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from common.log import log
from common.model import MappedBase
from core.config import settings


def create_database_url(unittest: bool = False) -> URL:
    """
    创建数据库链接

    :param unittest: 是否用于单元测试
    :return:
    """
    if settings.DATABASE_TYPE == 'sqlite':
        # SQLite数据库连接
        return URL.create(drivername='sqlite+aiosqlite', database=settings.DATABASE_SCHEMA)
    elif settings.DATABASE_TYPE == 'mysql':
        # MySQL数据库连接
        url = URL.create(
            drivername='mysql+asyncmy',
            username=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_SCHEMA if not unittest else f'{settings.DATABASE_SCHEMA}_test',
        )
        url.update_query_dict({'charset': settings.DATABASE_CHARSET})
        return url
    else:
        # PostgreSQL数据库连接
        url = URL.create(
            drivername='postgresql+asyncpg',
            username=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_SCHEMA if not unittest else f'{settings.DATABASE_SCHEMA}_test',
        )
        return url


def create_async_engine_and_session(url: str | URL) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """
    创建数据库引擎和 Session

    :param url: 数据库连接 URL
    :return:
    """
    try:
        # 数据库引擎配置
        engine_kwargs = {
            'url': url,
            'echo': settings.DATABASE_ECHO,
            'echo_pool': settings.DATABASE_POOL_ECHO,
            'future': True,
        }

        # SQLite不支持连接池配置
        if settings.DATABASE_TYPE != 'sqlite':
            engine_kwargs.update({
                'pool_size': 10,  # 低：- 高：+
                'max_overflow': 20,  # 低：- 高：+
                'pool_timeout': 30,  # 低：+ 高：-
                'pool_recycle': 3600,  # 低：+ 高：-
                'pool_pre_ping': True,  # 低：False 高：True
                'pool_use_lifo': False,  # 低：False 高：True
            })

        # 数据库引擎
        engine = create_async_engine(**engine_kwargs)
    except Exception as e:
        log.error('❌ 数据库链接失败 {}', e)
        sys.exit()
    else:
        db_session = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autoflush=False,  # 禁用自动刷新
            expire_on_commit=False,  # 禁用提交时过期
        )
        return engine, db_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with async_db_session() as session:
        yield session


async def create_tables() -> None:
    """创建数据库表"""
    async with async_engine.begin() as coon:
        await coon.run_sync(MappedBase.metadata.create_all)


def uuid4_str() -> str:
    """数据库引擎 UUID 类型兼容性解决方案"""
    return str(uuid4())


# SQLA 数据库链接
SQLALCHEMY_DATABASE_URL = create_database_url()

# SALA 异步引擎和会话
async_engine, async_db_session = create_async_engine_and_session(SQLALCHEMY_DATABASE_URL)

# Session Annotated
CurrentSession = Annotated[AsyncSession, Depends(get_db)]
