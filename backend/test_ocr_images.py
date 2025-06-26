#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OCR图片功能
"""

import requests
import json
from pathlib import Path

# API基础URL
BASE_URL = "http://127.0.0.1:8000"

def test_ocr_images_api():
    """测试OCR图片相关API"""
    
    print("🧪 开始测试OCR图片功能...")
    
    # 测试视频ID
    video_id = 1
    
    try:
        # 1. 获取OCR存储信息
        print(f"\n📊 获取视频 {video_id} 的OCR存储信息...")
        response = requests.get(f"{BASE_URL}/videos/{video_id}/ocr-storage-info")
        if response.status_code == 200:
            storage_info = response.json()
            print(f"✅ OCR存储信息: {json.dumps(storage_info, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取OCR存储信息失败: {response.status_code} - {response.text}")
        
        # 2. 获取OCR图片列表
        print(f"\n🖼️ 获取视频 {video_id} 的OCR图片列表...")
        response = requests.get(f"{BASE_URL}/videos/{video_id}/ocr-images")
        if response.status_code == 200:
            ocr_images = response.json()
            print(f"✅ OCR图片列表: {json.dumps(ocr_images, indent=2, ensure_ascii=False)}")
            
            # 3. 如果有OCR图片，测试查看功能
            if ocr_images:
                first_image = ocr_images[0]
                frame_id = first_image['frame_id']
                
                print(f"\n👁️ 测试查看帧 {frame_id} 的OCR图片...")
                response = requests.get(f"{BASE_URL}/videos/{video_id}/frames/{frame_id}/ocr-image")
                if response.status_code == 200:
                    print(f"✅ 成功获取OCR图片，大小: {len(response.content)} 字节")
                    
                    # 保存测试图片到本地
                    test_image_path = Path(f"test_ocr_image_frame_{frame_id}.jpg")
                    with open(test_image_path, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ 测试图片已保存到: {test_image_path}")
                else:
                    print(f"❌ 获取OCR图片失败: {response.status_code} - {response.text}")
            else:
                print("ℹ️ 没有找到OCR图片")
        else:
            print(f"❌ 获取OCR图片列表失败: {response.status_code} - {response.text}")
        
        # 4. 测试系统信息
        print(f"\n🔧 获取系统信息...")
        response = requests.get(f"{BASE_URL}/system/info")
        if response.status_code == 200:
            system_info = response.json()
            print(f"✅ 系统信息: {json.dumps(system_info, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取系统信息失败: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保后端服务正在运行 (python main.py)")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    
    print("\n🏁 OCR图片功能测试完成")

if __name__ == "__main__":
    test_ocr_images_api()