#!/usr/bin/env python3

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp

from common import __version__
from common.log import set_custom_logfile, setup_logging
from core.config import settings
from core.path_config import STATIC_DIR, UPLOAD_DIR
from database.db import create_tables
from database.redis import redis_client
from middleware.access_middleware import AccessMiddleware
from utils.check import ensure_unique_route_names, http_limit_callback


@asynccontextmanager
async def register_init(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    启动初始化

    :param app: FastAPI 应用实例
    :return:
    """
    # 创建数据库表
    await create_tables()

    # 初始化 redis
    await redis_client.open()

    # 初始化 limiter
    await FastAPILimiter.init(
        redis=redis_client,
        prefix=settings.REQUEST_LIMITER_REDIS_PREFIX,
        http_callback=http_limit_callback,
    )

    # 创建操作日志任务
    # create_task(OperaLogMiddleware.consumer())

    yield

    # 关闭 redis 连接
    await redis_client.aclose()


def register_app() -> FastAPI:
    """注册 FastAPI 应用"""

    class MyFastAPI(FastAPI):
        if settings.MIDDLEWARE_CORS:
            # Related issues
            # https://github.com/fastapi/fastapi/discussions/7847
            # https://github.com/fastapi/fastapi/discussions/8027
            def build_middleware_stack(self) -> ASGIApp:
                return CORSMiddleware(
                    super().build_middleware_stack(),
                    allow_origins=settings.CORS_ALLOWED_ORIGINS,
                    allow_credentials=True,
                    allow_methods=['*'],
                    allow_headers=['*'],
                    expose_headers=settings.CORS_EXPOSE_HEADERS,
                )

    app = MyFastAPI(
        version=__version__,
        lifespan=register_init,
    )

    # 注册组件
    register_logger()
    register_static_file(app)
    register_middleware(app)
    register_router(app)
    register_page(app)

    return app


def register_logger() -> None:
    """注册日志"""
    setup_logging()
    set_custom_logfile()


def register_static_file(app: FastAPI) -> None:
    """
    注册静态资源服务

    :param app: FastAPI 应用实例
    :return:
    """
    # 上传静态资源
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    app.mount('/static/upload', StaticFiles(directory=UPLOAD_DIR), name='upload')

    # 固有静态资源
    if settings.FASTAPI_STATIC_FILES:
        app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


def register_middleware(app: FastAPI) -> None:
    """
    注册中间件（执行顺序从下往上）

    :param app: FastAPI 应用实例
    :return:
    """
    # Opera log
    # app.add_middleware(OperaLogMiddleware)

    # State
    # app.add_middleware(StateMiddleware)

    # JWT auth
    # app.add_middleware(
    #     AuthenticationMiddleware,
    #     backend=JwtAuthMiddleware(),
    #     on_error=JwtAuthMiddleware.auth_exception_handler,
    # )

    # I18n
    # app.add_middleware(I18nMiddleware)

    # Access log
    app.add_middleware(AccessMiddleware)

    # Trace ID
    app.add_middleware(CorrelationIdMiddleware, validator=False)


def register_router(app: FastAPI) -> None:
    """
    注册路由

    :param app: FastAPI 应用实例
    :return:
    """
    from app.api.routers import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Extra
    # ensure_unique_route_names(app)


def register_page(app: FastAPI) -> None:
    """
    注册分页查询功能

    :param app: FastAPI 应用实例
    :return:
    """
    add_pagination(app)
