#!/usr/bin/env python3
"""
简单测试脚本
"""
import requests
import json

def test_guest_login():
    """测试访客登录"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/auth/guest", timeout=10)
        print(f"访客登录状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"成功! 用户ID: {data['user']['id']}")
            print(f"邮箱: {data['user']['email']}")
            return True
        else:
            print(f"失败: {response.text}")
            return False
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_health():
    """测试健康检查"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=5)
        print(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {response.json()}")
            return True
        else:
            print(f"失败: {response.text}")
            return False
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    print("=== 简单测试 ===")
    
    print("\n1. 测试健康检查:")
    test_health()
    
    print("\n2. 测试访客登录:")
    test_guest_login()
    
    print("\n=== 测试完成 ===")
