#!/usr/bin/env python3
"""
简单的API测试脚本
"""
import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_health():
    """测试健康检查"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_guest_login():
    """测试访客登录"""
    try:
        response = requests.get(f"{BASE_URL}/auth/guest")
        print(f"Guest login: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Guest login failed: {e}")
        return False

def test_image_generation():
    """测试图片生成"""
    try:
        data = {
            "prompt": "一只可爱的小猫",
            "style": "realistic",
            "size": "1024x1024"
        }
        response = requests.post(f"{BASE_URL}/generate-image", json=data)
        print(f"Image generation: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Generated image success: {result.get('success')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Image generation failed: {e}")
        return False

def test_content_rewrite():
    """测试文案改写"""
    try:
        data = {
            "originalContent": "这是一段测试文本",
            "rewriteType": "make_professional",
            "targetTone": "professional"
        }
        response = requests.post(f"{BASE_URL}/rewrite-content", json=data)
        print(f"Content rewrite: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Rewritten content: {result.get('rewrittenContent')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Content rewrite failed: {e}")
        return False

def test_xhs_share():
    """测试小红书分享配置"""
    try:
        data = {
            "type": "normal",
            "title": "测试标题",
            "content": "测试内容",
            "url": "https://example.com"
        }
        response = requests.post(f"{BASE_URL}/xhs/share-config", json=data)
        print(f"XHS share config: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Share config generated: {result.get('shareInfo', {}).get('title')}")
        return response.status_code == 200
    except Exception as e:
        print(f"XHS share config failed: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始测试API接口...")
    print("=" * 50)
    
    tests = [
        ("健康检查", test_health),
        ("访客登录", test_guest_login),
        ("图片生成", test_image_generation),
        ("文案改写", test_content_rewrite),
        ("小红书分享", test_xhs_share),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n测试: {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
        print(f"结果: {'✓ 成功' if success else '✗ 失败'}")
    
    print("\n" + "=" * 50)
    print("测试总结:")
    for test_name, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {test_name}: {status}")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    print(f"\n总计: {success_count}/{total_count} 个测试通过")

if __name__ == "__main__":
    main()
