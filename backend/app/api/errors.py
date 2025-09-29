"""与NextJS ChatSDK错误响应保持一致的工具方法。"""

from __future__ import annotations

import logging
from typing import Final

from fastapi.responses import JSONResponse

LOGGER = logging.getLogger("chat.errors")

STATUS_CODE_BY_ERROR_TYPE: Final = {
    "bad_request": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "rate_limit": 429,
    "offline": 503,
}

VISIBILITY_BY_SURFACE: Final = {
    "database": "log",
    "chat": "response",
    "auth": "response",
    "stream": "response",
    "api": "response",
    "history": "response",
    "vote": "response",
    "document": "response",
    "suggestions": "response",
    "activate_gateway": "response",
    "image_generation": "response",
    "content_rewrite": "response",
}

DEFAULT_MESSAGE: Final = "Something went wrong. Please try again later."

MESSAGES_BY_CODE: Final = {
    "bad_request:api": "The request couldn't be processed. Please check your input and try again.",
    "bad_request:activate_gateway": (
        "AI Gateway requires a valid credit card on file to service requests. Please visit "
        "https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai%3Fmodal%3Dadd-credit-card to add a card "
        "and unlock your free credits."
    ),
    "unauthorized:auth": "You need to sign in before continuing.",
    "forbidden:auth": "Your account does not have access to this feature.",
    "rate_limit:chat": "You have exceeded your maximum number of messages for the day. Please try again later.",
    "not_found:chat": "The requested chat was not found. Please check the chat ID and try again.",
    "forbidden:chat": "This chat belongs to another user. Please check the chat ID and try again.",
    "unauthorized:chat": "You need to sign in to view this chat. Please sign in and try again.",
    "offline:chat": "We're having trouble sending your message. Please check your internet connection and try again.",
    "not_found:document": "The requested document was not found. Please check the document ID and try again.",
    "forbidden:document": "This document belongs to another user. Please check the document ID and try again.",
    "unauthorized:document": "You need to sign in to view this document. Please sign in and try again.",
    "bad_request:document": "The request to create or update the document was invalid. Please check your input and try again.",
    "unauthorized:image_generation": "You need to sign in to generate images. Please sign in and try again.",
    "rate_limit:image_generation": "You have exceeded your image generation limit. Please try again later.",
    "offline:image_generation": "Image generation service is currently unavailable. Please try again later.",
    "unauthorized:content_rewrite": "You need to sign in to rewrite content. Please sign in and try again.",
    "rate_limit:content_rewrite": "You have exceeded your content rewriting limit. Please try again later.",
    "offline:content_rewrite": "Content rewriting service is currently unavailable. Please try again later.",
}


def error_response(error_code: str, cause: str | None = None) -> JSONResponse:
    """按照NextJS实现返回统一错误响应。"""

    parts = error_code.split(":", maxsplit=1)
    if len(parts) != 2:
        raise ValueError("error_code must use the format '<type>:<surface>'.")

    error_type, surface = parts
    status_code = STATUS_CODE_BY_ERROR_TYPE.get(error_type, 500)
    visibility = VISIBILITY_BY_SURFACE.get(surface, "response")

    if visibility == "log":
        LOGGER.error("%s", {"code": error_code, "cause": cause})
        return JSONResponse(
            status_code=status_code,
            content={"code": "", "message": DEFAULT_MESSAGE},
        )

    message = MESSAGES_BY_CODE.get(error_code, DEFAULT_MESSAGE)
    return JSONResponse(
        status_code=status_code,
        content={"code": error_code, "message": message, "cause": cause},
    )
