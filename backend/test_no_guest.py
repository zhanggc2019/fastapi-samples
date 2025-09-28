#!/usr/bin/env python3
"""
测试访客登录是否已被移除
"""
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_guest_login_removed():
    """测试访客登录是否已被移除"""
    print("测试访客登录是否已被移除...")
    
    try:
        response = requests.get(f"{BASE_URL}/auth/guest", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ 访客登录已成功移除（404 Not Found）")
            return True
        else:
            print(f"❌ 访客登录仍然存在: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_register_still_works():
    """测试注册功能是否仍然正常"""
    print("\n测试注册功能是否仍然正常...")
    
    import random
    random_id = random.randint(10000, 99999)
    email = f"test_no_guest_{random_id}@example.com"
    
    data = {
        "email": email,
        "password": "test123456",
        "confirm_password": "test123456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 注册功能正常工作")
            print(f"   用户ID: {result['user']['id']}")
            return True
        else:
            print(f"❌ 注册功能异常: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 注册请求失败: {e}")
        return False

def test_login_still_works():
    """测试登录功能是否仍然正常"""
    print("\n测试登录功能是否仍然正常...")
    
    data = {
        "grant_type": "password",
        "username": "1072238017@qq.com",
        "password": "1072238017@qq.com"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 登录功能正常工作")
            print(f"   用户ID: {result['user']['id']}")
            return True
        else:
            print(f"❌ 登录功能异常: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 登录请求失败: {e}")
        return False

def main():
    print("🚀 测试访客登录移除后的系统状态...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 1. 测试访客登录是否已移除
    if test_guest_login_removed():
        success_count += 1
    
    # 2. 测试注册功能是否正常
    if test_register_still_works():
        success_count += 1
    
    # 3. 测试登录功能是否正常
    if test_login_still_works():
        success_count += 1
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    print(f"📊 成功率: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    if success_count == total_tests:
        print("🎯 访客登录已成功移除，其他功能正常！")
    else:
        print(f"⚠️  有 {total_tests - success_count} 个测试失败。")

if __name__ == "__main__":
    main()
