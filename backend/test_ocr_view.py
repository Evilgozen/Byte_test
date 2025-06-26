#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR结果查看功能测试脚本
"""

import requests
import json
from typing import Dict, Any

# 配置
BASE_URL = "http://127.0.0.1:8000"
VIDEO_ID = 1  # 测试用的视频ID

def test_get_ocr_results():
    """测试获取OCR结果接口"""
    print("\n=== 测试获取OCR结果接口 ===")
    
    url = f"{BASE_URL}/videos/{VIDEO_ID}/ocr-results"
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"数据库OCR结果数量: {len(results)}")
            if results:
                print("第一条结果示例:")
                print(json.dumps(results[0], indent=2, ensure_ascii=False))
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_get_enhanced_ocr_results():
    """测试获取增强OCR结果接口"""
    print("\n=== 测试获取增强OCR结果接口 ===")
    
    url = f"{BASE_URL}/videos/{VIDEO_ID}/enhanced-ocr-results"
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"JSON文件OCR结果数量: {len(results)}")
            if results:
                print("第一条结果示例:")
                result = results[0]
                print(f"  frame_id: {result.get('frame_id')}")
                print(f"  frame_path: {result.get('frame_path')}")
                print(f"  ocr_version: {result.get('ocr_version')}")
                print(f"  processing_time: {result.get('processing_time')}")
                print(f"  text_blocks数量: {len(result.get('text_blocks', []))}")
                print(f"  是否有raw_result: {result.get('raw_result') is not None}")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_view_ocr_results():
    """测试查看OCR结果接口（新增）"""
    print("\n=== 测试查看OCR结果接口（新增） ===")
    
    url = f"{BASE_URL}/videos/{VIDEO_ID}/ocr-results/view"
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            
            print("\n统计信息:")
            print(f"  视频ID: {stats.get('video_id')}")
            print(f"  数据库记录数: {stats.get('database_records_count')}")
            print(f"  JSON文件数: {stats.get('json_files_count')}")
            print(f"  数据一致性: {stats.get('data_consistency')}")
            
            db_results = data.get('database_results', [])
            json_results = data.get('json_results', [])
            
            print(f"\n数据库结果示例 (共{len(db_results)}条):")
            if db_results:
                result = db_results[0]
                print(f"  ID: {result.get('id')}")
                print(f"  Frame ID: {result.get('frame_id')}")
                print(f"  文本内容: {result.get('text_content', '')[:50]}...")
                print(f"  置信度: {result.get('confidence')}")
                print(f"  处理时间: {result.get('processed_at')}")
            
            print(f"\nJSON文件结果示例 (共{len(json_results)}条):")
            if json_results:
                result = json_results[0]
                print(f"  Frame ID: {result.get('frame_id')}")
                print(f"  Frame Path: {result.get('frame_path')}")
                print(f"  OCR版本: {result.get('ocr_version')}")
                print(f"  处理时间: {result.get('processing_time')}s")
                print(f"  文本块数量: {result.get('text_blocks_count')}")
                print(f"  有原始结果: {result.get('has_raw_result')}")
                
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def main():
    """主函数"""
    print("OCR结果查看功能测试")
    print(f"测试视频ID: {VIDEO_ID}")
    print(f"后端地址: {BASE_URL}")
    
    # 测试各个接口
    test_get_ocr_results()
    test_get_enhanced_ocr_results()
    test_view_ocr_results()
    
    print("\n=== 测试完成 ===")
    print("\n说明:")
    print("1. 数据库结果：存储简化的OCR信息（文本、置信度、边界框）")
    print("2. JSON文件结果：存储完整的OCR处理结果（包含原始数据、处理时间等）")
    print("3. 查看接口：同时显示两种数据源的信息和统计")

if __name__ == "__main__":
    main()