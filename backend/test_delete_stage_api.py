#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试删除阶段配置接口
"""

import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000"

def test_delete_stage_apis():
    """测试删除阶段配置的API"""
    print("=== 删除阶段配置API测试 ===")
    
    try:
        # 1. 首先查看现有的阶段配置
        print("\n1. 查看视频1的现有阶段配置:")
        response = requests.get(f"{BASE_URL}/videos/1/stage-configs/")
        if response.status_code == 200:
            configs = response.json()
            print(f"找到 {len(configs)} 个阶段配置:")
            for config in configs:
                print(f"  - ID: {config['id']}, 名称: {config['stage_name']}, 顺序: {config['stage_order']}")
        else:
            print(f"获取阶段配置失败: {response.status_code} - {response.text}")
            return
        
        if not configs:
            print("没有阶段配置，先创建一个测试配置")
            # 创建测试配置
            test_config = {
                "video_id": 1,
                "stage_name": "测试删除阶段",
                "stage_order": 999,
                "keywords": ["测试", "删除"],
                "start_rule": {"type": "keyword_appear", "keywords": ["测试"]},
                "end_rule": {"type": "keyword_disappear", "keywords": ["删除"]}
            }
            
            response = requests.post(f"{BASE_URL}/stage-configs/", json=test_config)
            if response.status_code == 200:
                new_config = response.json()
                print(f"创建测试配置成功: ID {new_config['id']}")
                configs = [new_config]
            else:
                print(f"创建测试配置失败: {response.status_code} - {response.text}")
                return
        
        # 2. 测试删除单个阶段配置
        if configs:
            config_to_delete = configs[0]
            print(f"\n2. 测试删除单个阶段配置 (ID: {config_to_delete['id']}):")
            
            response = requests.delete(f"{BASE_URL}/stage-configs/{config_to_delete['id']}")
            if response.status_code == 200:
                result = response.json()
                print(f"删除成功: {result}")
            else:
                print(f"删除失败: {response.status_code} - {response.text}")
        
        # 3. 验证删除结果
        print("\n3. 验证删除结果:")
        response = requests.get(f"{BASE_URL}/videos/1/stage-configs/")
        if response.status_code == 200:
            remaining_configs = response.json()
            print(f"剩余 {len(remaining_configs)} 个阶段配置")
            for config in remaining_configs:
                print(f"  - ID: {config['id']}, 名称: {config['stage_name']}")
        
        # 4. 测试删除不存在的配置
        print("\n4. 测试删除不存在的配置:")
        response = requests.delete(f"{BASE_URL}/stage-configs/99999")
        if response.status_code == 404:
            print("正确返回404错误")
        else:
            print(f"意外的响应: {response.status_code} - {response.text}")
        
        # 5. 如果还有配置，测试批量删除
        if remaining_configs:
            print("\n5. 测试批量删除视频的所有阶段配置:")
            response = requests.delete(f"{BASE_URL}/videos/1/stage-configs/")
            if response.status_code == 200:
                result = response.json()
                print(f"批量删除成功: {result}")
            else:
                print(f"批量删除失败: {response.status_code} - {response.text}")
            
            # 验证批量删除结果
            response = requests.get(f"{BASE_URL}/videos/1/stage-configs/")
            if response.status_code == 200:
                final_configs = response.json()
                print(f"最终剩余 {len(final_configs)} 个阶段配置")
        
        # 6. 测试删除不存在视频的配置
        print("\n6. 测试删除不存在视频的配置:")
        response = requests.delete(f"{BASE_URL}/videos/99999/stage-configs/")
        if response.status_code == 404:
            print("正确返回404错误")
        else:
            print(f"意外的响应: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("无法连接到API服务器，请确保服务器正在运行 (python main.py)")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_delete_stage_apis()