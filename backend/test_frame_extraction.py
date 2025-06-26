#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频分帧功能测试脚本
"""

import requests
import json
from pathlib import Path

# API基础URL
BASE_URL = "http://127.0.0.1:8000"

def test_frame_extraction():
    """测试视频分帧功能"""
    print("=== 视频分帧功能测试 ===")
    
    # 1. 获取系统信息
    print("\n1. 获取系统信息...")
    response = requests.get(f"{BASE_URL}/system/info")
    if response.status_code == 200:
        info = response.json()
        print(f"   项目数量: {info['database']['projects']}")
        print(f"   视频数量: {info['database']['videos']}")
    else:
        print(f"   获取系统信息失败: {response.status_code}")
        return
    
    # 2. 获取所有项目
    print("\n2. 获取项目列表...")
    response = requests.get(f"{BASE_URL}/projects/")
    if response.status_code == 200:
        projects = response.json()
        if not projects:
            print("   没有找到项目")
            return
        project = projects[0]
        project_id = project['id']
        print(f"   使用项目: {project['name']} (ID: {project_id})")
    else:
        print(f"   获取项目失败: {response.status_code}")
        return
    
    # 3. 获取项目的视频
    print(f"\n3. 获取项目 {project_id} 的视频...")
    response = requests.get(f"{BASE_URL}/projects/{project_id}/videos/")
    if response.status_code == 200:
        videos = response.json()
        if not videos:
            print("   项目中没有视频")
            return
        video = videos[0]
        video_id = video['id']
        print(f"   使用视频: {video['original_filename']} (ID: {video_id})")
        print(f"   视频状态: {video['process_status']}")
    else:
        print(f"   获取视频失败: {response.status_code}")
        return
    
    # 4. 检查视频是否已有帧
    print(f"\n4. 检查视频 {video_id} 的现有帧...")
    response = requests.get(f"{BASE_URL}/videos/{video_id}/frames")
    if response.status_code == 200:
        existing_frames = response.json()
        print(f"   现有帧数量: {len(existing_frames)}")
        if existing_frames:
            print("   已存在帧，跳过分帧处理")
            # 显示前几个帧的信息
            for i, frame in enumerate(existing_frames[:3]):
                print(f"   帧 {i+1}: 帧号={frame['frame_number']}, 时间戳={frame['timestamp_ms']}ms")
            return
    else:
        print(f"   获取帧列表失败: {response.status_code}")
    
    # 5. 执行视频分帧
    print(f"\n5. 开始视频分帧处理...")
    frame_request = {
        "fps": 3,  # 每2秒提取一帧
        "quality": 85,
        "max_frames": 500  # 最多提取10帧
    }
    
    response = requests.post(
        f"{BASE_URL}/videos/{video_id}/extract-frames",
        json=frame_request
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   分帧成功!")
        print(f"   总帧数: {result['total_frames']}")
        print("   帧信息:")
        for frame in result['frames'][:5]:  # 显示前5帧
            print(f"     帧号={frame['frame_number']}, 时间戳={frame['timestamp_ms']}ms, 大小={frame['file_size']}字节")
    else:
        print(f"   分帧失败: {response.status_code}")
        print(f"   错误信息: {response.text}")
        return
    
    # 6. 获取分帧后的帧列表
    print(f"\n6. 获取分帧后的帧列表...")
    response = requests.get(f"{BASE_URL}/videos/{video_id}/frames")
    if response.status_code == 200:
        frames = response.json()
        print(f"   帧数量: {len(frames)}")
        
        # 测试获取第一帧图片
        if frames:
            first_frame = frames[0]
            frame_id = first_frame['id']
            print(f"\n7. 测试获取帧图片 (帧ID: {frame_id})...")
            
            # 获取帧图片URL
            image_url = f"{BASE_URL}/frames/{frame_id}/image"
            response = requests.get(image_url)
            
            if response.status_code == 200:
                print(f"   帧图片获取成功")
                print(f"   图片URL: {image_url}")
                print(f"   内容类型: {response.headers.get('content-type')}")
                print(f"   文件大小: {len(response.content)} 字节")
            else:
                print(f"   获取帧图片失败: {response.status_code}")
    else:
        print(f"   获取帧列表失败: {response.status_code}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    try:
        test_frame_extraction()
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到后端服务，请确保后端服务正在运行")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")