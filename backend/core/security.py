from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext
from app.models import User
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

# 虚拟密码，用于防止时序攻击
DUMMY_PASSWORD = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"


def create_access_token(subject: str | Any, expires_delta: timedelta, user: User) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}

    to_encode["id"] = user.id
    to_encode["email"] = user.email
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def authenticate_user(db, email: str, password: str)-> User | None:
    """验证用户凭据"""
    from sqlalchemy import select


    # 查询用户
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        return None

    if not user.password:
        return None

    if not verify_password(password, user.password):
        return None

    return user


# 访客用户功能已取消
