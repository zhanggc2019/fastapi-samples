#!/usr/bin/env python3
"""
测试完整的认证系统
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_guest_login():
    """测试访客登录"""
    print("=== 测试访客登录 ===")
    response = requests.get(f"{BASE_URL}/auth/guest")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"访问令牌: {data['access_token'][:50]}...")
        print(f"用户ID: {data['user']['id']}")
        print(f"用户邮箱: {data['user']['email']}")
        return data['access_token']
    else:
        print(f"错误: {response.text}")
        return None

def test_authenticated_request(token):
    """测试需要认证的请求"""
    print("\n=== 测试认证请求 ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试图片生成接口
    payload = {
        "prompt": "一只可爱的小猫",
        "style": "realistic",
        "size": "512x512"
    }
    
    response = requests.post(f"{BASE_URL}/generate-image", 
                           headers=headers, 
                           json=payload)
    print(f"图片生成状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"生成成功: {data.get('success', False)}")
        print(f"提示词: {data.get('prompt', '')}")
    else:
        print(f"错误: {response.text}")

def test_regular_login():
    """测试常规用户登录"""
    print("\n=== 测试常规用户登录 ===")
    
    # 首先创建一个用户（这里简化，实际应该有注册接口）
    login_data = {
        "username": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    print(f"登录状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"访问令牌: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"登录失败: {response.text}")
        return None

def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"健康检查状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {response.json()}")

def main():
    print("开始测试完整的认证系统...")
    
    # 测试健康检查
    test_health_check()
    
    # 测试访客登录
    guest_token = test_guest_login()
    
    if guest_token:
        # 测试认证请求
        test_authenticated_request(guest_token)
    
    # 测试常规用户登录
    regular_token = test_regular_login()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()
