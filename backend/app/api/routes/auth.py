import uuid
from typing import Any
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep
from app.models import (
    User, UserRegister, LoginRequest, LoginResponse,
    RegisterResponse
)
from core.security import (
    authenticate_user, create_access_token,
    get_password_hash
)
from sqlalchemy import select
from core.config import settings

router = APIRouter()

@router.post("/auth/login/access-token", response_model=LoginResponse)
@router.post("/auth/login", response_model=LoginResponse)
async def login(
    *,
    db: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    用户登录
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
        user=user
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.post("/auth/login/credentials", response_model=LoginResponse)
async def login_credentials(
    *,
    db: SessionDep,
    login_data: LoginRequest
) -> Any:
    """
    使用JSON格式登录
    """
    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
        user=user
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


# 游客登录功能已取消


@router.post("/auth/register", response_model=RegisterResponse)
async def register(
    *,
    db: SessionDep,
    register_data: UserRegister
) -> Any:
    """
    用户注册
    """
    # 验证密码确认
    if register_data.password != register_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码和确认密码不匹配"
        )

    # 检查邮箱是否已存在
    statement = select(User).where(User.email == register_data.email)
    result = await db.execute(statement)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )

    try:
        # 创建新用户
        hashed_password = get_password_hash(register_data.password)
        user = User(
            email=register_data.email,
            password=hashed_password,
            is_active=True
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires,
            user=user
        )

        return RegisterResponse(
            access_token=access_token,
            token_type="bearer",
            user=user,
            message="注册成功"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )
