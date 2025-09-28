#!/usr/bin/env python3
"""
测试登录和主要API功能
"""
import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000/api"

def test_regular_login():
    """测试常规用户登录"""
    print("1. 测试常规用户登录...")
    data = {
        "grant_type": "password",
        "username": "1072238017@qq.com",
        "password": "1072238017@qq.com"
    }
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        user_id = data["user"]["id"]
        print(f"   ✅ 成功，用户ID: {user_id}")
        print(f"   🔑 Token: {token[:50]}...")
        return token, user_id
    else:
        print(f"   ❌ 失败: {response.text}")
        return None, None

def test_guest_login():
    """测试访客登录"""
    print("\n2. 测试访客登录...")
    response = requests.get(f"{BASE_URL}/auth/guest")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        user_id = data["user"]["id"]
        print(f"   ✅ 成功，访客ID: {user_id}")
        return token, user_id
    else:
        print(f"   ❌ 失败: {response.text}")
        return None, None

def test_chat_history(token):
    """测试聊天历史"""
    print("\n3. 测试聊天历史...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/history", headers=headers)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功，历史记录数量: {len(data)}")
        return True
    else:
        print(f"   ❌ 失败: {response.text}")
        return False

def test_content_rewrite(token):
    """测试文案改写"""
    print("\n4. 测试文案改写...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "originalContent": "这是一段测试文本，需要改写得更专业一些。",
        "rewriteType": "make_professional",
        "targetTone": "professional",
        "targetAudience": "商务人士"
    }
    response = requests.post(f"{BASE_URL}/rewrite-content", json=data, headers=headers)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功")
        print(f"   📝 原文: {result.get('originalContent', '')[:50]}...")
        print(f"   ✨ 改写: {result.get('rewrittenContent', '')[:50]}...")
        return True
    else:
        print(f"   ❌ 失败: {response.text}")
        return False

def test_xhs_share():
    """测试小红书分享"""
    print("\n5. 测试小红书分享...")
    data = {
        "type": "image",
        "title": "AI生成的精美图片分享",
        "content": "这是一张由AI生成的精美图片，展现了现代科技的魅力。非常适合在小红书上分享，能够吸引更多用户的关注。",
        "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        "cover": "https://example.com/cover.jpg"
    }
    response = requests.post(f"{BASE_URL}/xhs/share-config", json=data)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功")
        print(f"   📱 平台: {result.get('shareInfo', {}).get('platform', 'N/A')}")
        print(f"   🏷️  标签: {result.get('shareInfo', {}).get('tags', [])}")
        return True
    else:
        print(f"   ❌ 失败: {response.text}")
        return False

def test_document_operations(token):
    """测试文档操作"""
    print("\n6. 测试文档操作...")
    headers = {"Authorization": f"Bearer {token}"}
    doc_id = str(uuid.uuid4())
    
    # 6.1 保存文档
    print("   6.1 保存文档...")
    doc_data = {
        "title": "测试文档标题",
        "content": "这是一个测试文档的内容，包含了一些示例文本。",
        "kind": "text"
    }
    save_response = requests.post(
        f"{BASE_URL}/document?id={doc_id}",
        json=doc_data,
        headers=headers
    )
    print(f"       保存状态码: {save_response.status_code}")
    
    if save_response.status_code == 200:
        print("       ✅ 文档保存成功")
        
        # 6.2 获取文档
        print("   6.2 获取文档...")
        get_response = requests.get(
            f"{BASE_URL}/document?id={doc_id}",
            headers=headers
        )
        print(f"       获取状态码: {get_response.status_code}")
        
        if get_response.status_code == 200:
            docs = get_response.json()
            print(f"       ✅ 文档获取成功，版本数量: {len(docs)}")
            return True
        else:
            print(f"       ❌ 文档获取失败: {get_response.text}")
            return False
    else:
        print(f"       ❌ 文档保存失败: {save_response.text}")
        return False

def main():
    print("🚀 开始测试登录和主要API功能...")
    print("=" * 60)
    
    success_count = 0
    total_tests = 6
    
    # 1. 常规用户登录
    regular_token, regular_user_id = test_regular_login()
    if regular_token:
        success_count += 1
    
    # 2. 访客登录
    guest_token, guest_user_id = test_guest_login()
    if guest_token:
        success_count += 1
    
    # 使用常规用户token进行后续测试
    test_token = regular_token if regular_token else guest_token
    
    if test_token:
        # 3. 聊天历史
        if test_chat_history(test_token):
            success_count += 1
        
        # 4. 文案改写
        if test_content_rewrite(test_token):
            success_count += 1
        
        # 6. 文档操作
        if test_document_operations(test_token):
            success_count += 1
    
    # 5. 小红书分享（不需要认证）
    if test_xhs_share():
        success_count += 1
    
    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print(f"📊 成功率: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    if success_count == total_tests:
        print("🎯 所有测试都通过了！API系统运行正常。")
    else:
        print(f"⚠️  有 {total_tests - success_count} 个测试失败，需要进一步检查。")

if __name__ == "__main__":
    main()
