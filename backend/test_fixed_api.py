#!/usr/bin/env python3
"""
测试修复后的API
"""
import requests
import json

def test_guest_login():
    """测试访客登录 - 新路径"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/auth/guest", timeout=10)
        print(f"访客登录状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功! 用户ID: {data['user']['id']}")
            print(f"   邮箱: {data['user']['email']}")
            print(f"   Token: {data['access_token'][:50]}...")
            return data['access_token']
        else:
            print(f"❌ 失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_chat_api(token):
    """测试聊天API - 新路径"""
    if not token:
        print("❌ 没有token，跳过聊天测试")
        return
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        chat_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "message": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "你好，请介绍一下自己"
                    }
                ]
            },
            "selectedChatModel": "chat-model",
            "selectedVisibilityType": "private"
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/api/chat", 
            headers=headers,
            json=chat_data,
            timeout=10
        )
        
        print(f"聊天API状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 聊天API成功!")
            # 读取流式响应的前几行
            content = response.text[:200]
            print(f"   响应内容: {content}...")
        else:
            print(f"❌ 聊天API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 聊天API错误: {e}")

def test_history_api(token):
    """测试历史记录API - 新路径"""
    if not token:
        print("❌ 没有token，跳过历史记录测试")
        return
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
        }
        
        response = requests.get(
            "http://127.0.0.1:8000/api/history", 
            headers=headers,
            timeout=10
        )
        
        print(f"历史记录API状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 历史记录API成功! 找到 {len(data)} 个聊天")
        else:
            print(f"❌ 历史记录API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 历史记录API错误: {e}")

def test_health():
    """测试健康检查 - 新路径"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
        print(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 健康检查成功: {response.json()}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 健康检查错误: {e}")
        return False

if __name__ == "__main__":
    print("=== 测试修复后的API ===")
    
    print("\n1. 测试健康检查 (新路径 /api/health):")
    test_health()
    
    print("\n2. 测试访客登录 (新路径 /api/auth/guest):")
    token = test_guest_login()
    
    print("\n3. 测试聊天API (新路径 /api/chat):")
    test_chat_api(token)
    
    print("\n4. 测试历史记录API (新路径 /api/history):")
    test_history_api(token)
    
    print("\n=== 测试完成 ===")
