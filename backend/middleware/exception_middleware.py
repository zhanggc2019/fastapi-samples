#!/usr/bin/env python3
"""统一异常处理中间件"""

import logging
import traceback
from typing import Any

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException

from common.log import log
from core.config import settings


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """统一异常处理中间件"""

    def __init__(self, app):
        super().__init__(app)
        # 创建文件日志处理器
        self.file_handler = self._setup_file_handler()
        
    def _setup_file_handler(self) -> logging.Handler:
        """设置文件日志处理器"""
        import os
        from logging.handlers import RotatingFileHandler

        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = os.path.join(log_dir, 'api_error.log')

        # 创建轮转文件处理器
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        return handler

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        处理请求并捕获异常

        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数

        Returns:
            Response: 响应对象
        """
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as exc:
            # HTTP异常，直接传递给FastAPI的异常处理器
            raise exc
            
        except (RequestValidationError, ValidationError) as exc:
            # 数据验证异常，记录日志但传递给FastAPI的异常处理器
            self._log_exception(request, exc, "Validation Error")
            raise exc
            
        except Exception as exc:
            # 其他未处理异常，记录日志并返回统一错误响应
            self._log_exception(request, exc, "Unhandled Exception")
            
            # 返回统一的错误响应
            return self._create_error_response(request, exc)
    
    def _log_exception(self, request: Request, exc: Exception, error_type: str = "Exception") -> None:
        """
        记录异常信息到控制台和文件
        
        Args:
            request: 请求对象
            exc: 异常对象
            error_type: 错误类型描述
        """
        # 获取请求信息
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        
        # 获取异常详细信息
        exc_type = type(exc).__name__
        exc_message = str(exc)
        exc_traceback = traceback.format_exc()
        
        # 构建日志消息
        log_message = (
            f"{error_type} in ASGI application - "
            f"Method: {method}, URL: {url}, Client IP: {client_ip}, "
            f"Exception: {exc_type}: {exc_message}"
        )
        
        # 记录到控制台
        log.error(log_message)
        
        # 记录详细堆栈信息到控制台（开发环境）
        if settings.ENVIRONMENT == 'dev':
            log.error(f"Exception traceback:\n{exc_traceback}")
        
        # 记录到文件
        file_logger = logging.getLogger('api_error')
        file_logger.setLevel(logging.ERROR)
        
        # 添加文件处理器（如果尚未添加）
        if not file_logger.handlers:
            file_logger.addHandler(self.file_handler)
        
        # 记录完整异常信息到文件
        file_logger.error(log_message)
        file_logger.error(f"Exception traceback:\n{exc_traceback}")
    
    def _create_error_response(self, request: Request, exc: Exception) -> JSONResponse:
        """
        创建统一的错误响应
        
        Args:
            request: 请求对象
            exc: 异常对象
            
        Returns:
            JSONResponse: 错误响应
        """
        # 获取异常类型和消息
        exc_type = type(exc).__name__
        exc_message = str(exc)
        
        # 根据环境返回不同的错误信息
        if settings.ENVIRONMENT == 'dev':
            # 开发环境：返回详细错误信息
            error_response = {
                "code": 500,
                "message": f"Internal Server Error: {exc_type}: {exc_message}",
                "error_type": exc_type,
                "detail": exc_message,
            }
        else:
            # 生产环境：返回通用错误信息
            error_response = {
                "code": 500,
                "message": "Internal Server Error",
            }
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )