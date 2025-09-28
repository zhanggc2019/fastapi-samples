#!/usr/bin/env python3
"""
创建测试用户
"""
import asyncio
from database.db import async_db_session
from app.models import User
from core.security import get_password_hash

async def create_test_user():
    """创建测试用户"""
    print("正在创建测试用户...")

    async with async_db_session() as db:
        # 检查用户是否已存在
        from sqlalchemy import select
        statement = select(User).where(User.email == "1072238017@qq.com")
        result = await db.execute(statement)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"用户已存在: {existing_user.email}")
            return
        
        # 创建新用户
        hashed_password = get_password_hash("1072238017@qq.com")
        user = User(
            email="1072238017@qq.com",
            password=hashed_password,
            is_active=True
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"✅ 测试用户创建成功:")
        print(f"   邮箱: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   激活状态: {user.is_active}")

if __name__ == "__main__":
    asyncio.run(create_test_user())
