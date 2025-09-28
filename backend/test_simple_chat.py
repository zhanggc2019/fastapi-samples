#!/usr/bin/env python3
"""
简单聊天测试
"""
import requests
import json
import uuid

# 先获取token
def get_token():
    response = requests.get("http://127.0.0.1:8000/api/auth/guest")
    if response.status_code == 200:
        return response.json()['access_token']
    return None

# 测试聊天API
def test_chat():
    token = get_token()
    if not token:
        print("无法获取token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 简化的聊天数据
    chat_data = {
        "id": str(uuid.uuid4()),
        "message": {
            "id": str(uuid.uuid4()),
            "role": "user",
            "parts": [{"type": "text", "text": "Hello"}],
            "attachments": []
        },
        "selectedChatModel": "gpt-4",
        "selectedVisibilityType": "private"
    }
    
    print("发送数据:")
    print(json.dumps(chat_data, indent=2))
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/chat",
            headers=headers,
            json=chat_data,
            timeout=10
        )
        
        print(f"\n状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_chat()
