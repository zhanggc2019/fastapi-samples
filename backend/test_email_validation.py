#!/usr/bin/env python3
"""
测试邮箱验证
"""
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_invalid_email():
    """测试无效邮箱"""
    print("测试无效邮箱验证...")
    
    data = {
        "email": "invalid-email-format",
        "password": "test123456",
        "confirm_password": "test123456"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")

if __name__ == "__main__":
    test_invalid_email()
