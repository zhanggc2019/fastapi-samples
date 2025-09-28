#!/usr/bin/env python3
"""
测试所有14个API接口
根据chat.json中定义的完整API列表进行测试
"""
import asyncio
import json
import uuid
from datetime import datetime
import httpx

BASE_URL = "http://127.0.0.1:8000/api"

async def test_all_apis():
    """测试所有14个API接口"""
    print("🚀 开始测试所有14个API接口...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # 1. 访客登录 - 获取token
        print("1️⃣  测试访客登录...")
        auth_response = await client.get(f"{BASE_URL}/auth/guest")
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            token = auth_data["access_token"]
            user_id = auth_data["user"]["id"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"   ✅ 访客登录成功，用户ID: {user_id}")
        else:
            print(f"   ❌ 访客登录失败: {auth_response.status_code}")
            return
        
        # 2. 发送聊天消息
        print("\n2️⃣  测试发送聊天消息...")
        chat_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        chat_request = {
            "id": chat_id,
            "message": {
                "id": message_id,
                "role": "user",
                "parts": [{"type": "text", "text": "你好，这是一个测试消息"}],
                "attachments": []
            },
            "selectedChatModel": "gpt-4",
            "selectedVisibilityType": "private"
        }
        
        chat_response = await client.post(
            f"{BASE_URL}/chat",
            json=chat_request,
            headers=headers
        )
        print(f"   📊 聊天消息状态: {chat_response.status_code}")
        
        # 3. 恢复聊天流
        print("\n3️⃣  测试恢复聊天流...")
        stream_response = await client.get(
            f"{BASE_URL}/chat/{chat_id}/stream",
            headers=headers
        )
        print(f"   📊 聊天流状态: {stream_response.status_code}")
        
        # 4. 获取聊天历史
        print("\n4️⃣  测试获取聊天历史...")
        history_response = await client.get(
            f"{BASE_URL}/history?limit=10",
            headers=headers
        )
        print(f"   📊 聊天历史状态: {history_response.status_code}")
        if history_response.status_code == 200:
            history_data = history_response.json()
            print(f"   📋 历史记录数量: {len(history_data)}")
        
        # 5. 生成图片
        print("\n5️⃣  测试生成图片...")
        image_request = {
            "prompt": "一只可爱的小猫在花园里玩耍",
            "style": "realistic",
            "size": "1024x1024"
        }
        image_response = await client.post(
            f"{BASE_URL}/generate-image",
            json=image_request,
            headers=headers
        )
        print(f"   📊 图片生成状态: {image_response.status_code}")
        
        # 6. 改写文案
        print("\n6️⃣  测试改写文案...")
        rewrite_request = {
            "originalContent": "这是一段需要改写的文本内容",
            "rewriteType": "make_professional",
            "targetTone": "professional",
            "targetAudience": "商务人士"
        }
        rewrite_response = await client.post(
            f"{BASE_URL}/rewrite-content",
            json=rewrite_request,
            headers=headers
        )
        print(f"   📊 文案改写状态: {rewrite_response.status_code}")
        
        # 7. 上传文件 (模拟)
        print("\n7️⃣  测试上传文件...")
        # 创建一个模拟的图片文件
        fake_image_content = b"fake image content for testing"
        files = {"file": ("test.png", fake_image_content, "image/png")}
        upload_response = await client.post(
            f"{BASE_URL}/files/upload",
            files=files,
            headers=headers
        )
        print(f"   📊 文件上传状态: {upload_response.status_code}")
        
        # 8. 保存文档
        print("\n8️⃣  测试保存文档...")
        doc_id = str(uuid.uuid4())
        doc_request = {
            "title": "测试文档",
            "content": "这是一个测试文档的内容",
            "kind": "text"
        }
        save_doc_response = await client.post(
            f"{BASE_URL}/document?id={doc_id}",
            json=doc_request,
            headers=headers
        )
        print(f"   📊 文档保存状态: {save_doc_response.status_code}")
        
        # 9. 获取文档
        print("\n9️⃣  测试获取文档...")
        get_doc_response = await client.get(
            f"{BASE_URL}/document?id={doc_id}",
            headers=headers
        )
        print(f"   📊 文档获取状态: {get_doc_response.status_code}")
        
        # 10. 删除文档
        print("\n🔟 测试删除文档...")
        timestamp = datetime.utcnow().isoformat()
        delete_doc_response = await client.delete(
            f"{BASE_URL}/document?id={doc_id}&timestamp={timestamp}",
            headers=headers
        )
        print(f"   📊 文档删除状态: {delete_doc_response.status_code}")
        
        # 11. 获取投票记录
        print("\n1️⃣1️⃣ 测试获取投票记录...")
        vote_get_response = await client.get(
            f"{BASE_URL}/vote?chatId={chat_id}",
            headers=headers
        )
        print(f"   📊 投票获取状态: {vote_get_response.status_code}")
        
        # 12. 投票
        print("\n1️⃣2️⃣ 测试投票...")
        vote_request = {
            "chatId": chat_id,
            "messageId": message_id,
            "type": "up"
        }
        vote_response = await client.patch(
            f"{BASE_URL}/vote",
            json=vote_request,
            headers=headers
        )
        print(f"   📊 投票状态: {vote_response.status_code}")
        
        # 13. 获取建议
        print("\n1️⃣3️⃣ 测试获取建议...")
        suggestions_response = await client.get(
            f"{BASE_URL}/suggestions?documentId={doc_id}",
            headers=headers
        )
        print(f"   📊 建议获取状态: {suggestions_response.status_code}")
        
        # 14. 小红书分享配置
        print("\n1️⃣4️⃣ 测试小红书分享配置...")
        xhs_request = {
            "type": "image",
            "title": "AI生成的精美图片",
            "content": "这是一张由AI生成的精美图片，展现了现代科技的魅力。",
            "images": ["https://example.com/image1.jpg"],
            "cover": "https://example.com/cover.jpg"
        }
        xhs_response = await client.post(
            f"{BASE_URL}/xhs/share-config",
            json=xhs_request
        )
        print(f"   📊 小红书分享状态: {xhs_response.status_code}")
        
        print("\n" + "=" * 60)
        print("🎉 所有14个API接口测试完成！")
        
        # 统计结果
        success_count = 0
        total_count = 14
        
        responses = [
            auth_response, chat_response, stream_response, history_response,
            image_response, rewrite_response, upload_response, save_doc_response,
            get_doc_response, delete_doc_response, vote_get_response, vote_response,
            suggestions_response, xhs_response
        ]
        
        for i, response in enumerate(responses, 1):
            if response.status_code in [200, 201, 204]:
                success_count += 1
                print(f"✅ API {i:2d}: 成功 ({response.status_code})")
            else:
                print(f"❌ API {i:2d}: 失败 ({response.status_code})")
        
        print(f"\n📊 测试结果: {success_count}/{total_count} 个API成功")
        print(f"🎯 成功率: {success_count/total_count*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_all_apis())
