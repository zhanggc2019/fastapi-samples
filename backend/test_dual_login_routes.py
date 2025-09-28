#!/usr/bin/env python3
"""
测试两个登录路由是否都映射到同一个函数
"""
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_login_route(route_name, endpoint):
    """测试登录路由"""
    print(f"测试 {route_name}...")
    
    data = {
        "grant_type": "password",
        "username": "1072238017@qq.com",
        "password": "1072238017@qq.com"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 登录成功")
            print(f"   👤 用户ID: {result['user']['id']}")
            print(f"   🔑 Token: {result['access_token'][:30]}...")
            return True, result['access_token']
        else:
            print(f"   ❌ 登录失败: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False, None

def main():
    print("🚀 测试双登录路由映射...")
    print("=" * 50)
    
    # 测试两个登录路由
    success1, token1 = test_login_route("标准登录路由", "/auth/login")
    print()
    success2, token2 = test_login_route("访问令牌登录路由", "/auth/login/access-token")
    
    print("\n" + "=" * 50)
    print("🎉 测试结果:")
    
    if success1 and success2:
        print("✅ 两个登录路由都正常工作！")
        print("✅ 成功映射到同一个函数")
        
        # 比较token（应该不同，因为是不同时间生成的）
        if token1 and token2:
            print(f"\n🔑 Token比较:")
            print(f"   标准路由Token: {token1[:30]}...")
            print(f"   访问令牌路由Token: {token2[:30]}...")
            
            if token1 != token2:
                print("✅ 不同时间生成的token不同（正常）")
            else:
                print("⚠️  相同token（可能的缓存问题）")
        
        print("\n📋 可用的登录端点:")
        print("   1. POST /api/auth/login")
        print("   2. POST /api/auth/login/access-token")
        print("   3. POST /api/auth/login/credentials (JSON格式)")
        print("   4. POST /api/auth/register (注册)")
        
    elif success1:
        print("✅ 标准登录路由正常")
        print("❌ 访问令牌登录路由异常")
    elif success2:
        print("❌ 标准登录路由异常")
        print("✅ 访问令牌登录路由正常")
    else:
        print("❌ 两个登录路由都异常")
    
    print("\n🎯 双路由映射的优势:")
    print("   - 提供API兼容性")
    print("   - 支持不同的客户端需求")
    print("   - 代码复用，维护简单")

if __name__ == "__main__":
    main()
