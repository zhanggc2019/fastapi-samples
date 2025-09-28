#!/usr/bin/env python3
"""
简化的API测试
"""
import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000/api"

def test_guest_login():
    """测试访客登录"""
    print("1. 测试访客登录...")
    response = requests.get(f"{BASE_URL}/auth/guest")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        user_id = data["user"]["id"]
        print(f"   ✅ 成功，用户ID: {user_id}")
        return token, user_id
    else:
        print(f"   ❌ 失败: {response.text}")
        return None, None

def test_chat_history(token):
    """测试聊天历史"""
    print("\n2. 测试聊天历史...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/history", headers=headers)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功，历史记录数量: {len(data)}")
    else:
        print(f"   ❌ 失败: {response.text}")

def test_image_generation(token):
    """测试图片生成"""
    print("\n3. 测试图片生成...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "prompt": "一只可爱的小猫",
        "style": "realistic",
        "size": "1024x1024"
    }
    response = requests.post(f"{BASE_URL}/generate-image", json=data, headers=headers)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ 成功")
    else:
        print(f"   ❌ 失败: {response.text}")

def test_content_rewrite(token):
    """测试文案改写"""
    print("\n4. 测试文案改写...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "originalContent": "这是一段测试文本",
        "rewriteType": "improve_clarity",
        "targetTone": "professional"
    }
    response = requests.post(f"{BASE_URL}/rewrite-content", json=data, headers=headers)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ 成功")
    else:
        print(f"   ❌ 失败: {response.text}")

def test_xhs_share():
    """测试小红书分享"""
    print("\n5. 测试小红书分享...")
    data = {
        "type": "image",
        "title": "测试标题",
        "content": "测试内容"
    }
    response = requests.post(f"{BASE_URL}/xhs/share-config", json=data)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ 成功")
    else:
        print(f"   ❌ 失败: {response.text}")

def main():
    print("🚀 开始简化API测试...")
    print("=" * 50)
    
    # 1. 访客登录
    token, user_id = test_guest_login()
    if not token:
        print("❌ 访客登录失败，停止测试")
        return
    
    # 2. 聊天历史
    test_chat_history(token)
    
    # 3. 图片生成
    test_image_generation(token)
    
    # 4. 文案改写
    test_content_rewrite(token)
    
    # 5. 小红书分享
    test_xhs_share()
    
    print("\n" + "=" * 50)
    print("🎉 简化测试完成！")

if __name__ == "__main__":
    main()
