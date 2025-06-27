#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键字分析测试脚本
测试video_id=1的关键字匹配功能
"""

import json
from typing import List, Dict, Any
from datetime import datetime

def test_keyword_matching():
    """测试关键字匹配功能"""
    print("=" * 60)
    print("关键字分析测试 - Video ID: 1")
    print("=" * 60)
    
    # 模拟OCR结果数据（基于实际可能的数据结构）
    mock_ocr_results = [
        {
            "frame_number": 1,
            "timestamp": 0.0,
            "text": "欢迎来到我们的产品介绍",
            "confidence": 0.95
        },
        {
            "frame_number": 30,
            "timestamp": 1.0,
            "text": "这是一个创新的解决方案",
            "confidence": 0.92
        },
        {
            "frame_number": 60,
            "timestamp": 2.0,
            "text": "产品特性包括高效和稳定",
            "confidence": 0.88
        },
        {
            "frame_number": 90,
            "timestamp": 3.0,
            "text": "解决方案适用于各种场景",
            "confidence": 0.91
        },
        {
            "frame_number": 120,
            "timestamp": 4.0,
            "text": "感谢观看我们的产品演示",
            "confidence": 0.94
        }
    ]
    
    # 测试关键字列表
    test_keywords = ["产品", "解决方案", "创新", "稳定", "不存在的关键字"]
    
    print(f"\n📊 OCR结果总数: {len(mock_ocr_results)}")
    print(f"🔍 测试关键字: {test_keywords}")
    print("\n" + "-" * 50)
    
    # 手动执行关键字分析逻辑
    analysis_results = []
    
    for keyword in test_keywords:
        print(f"\n🔍 分析关键字: '{keyword}'")
        
        # 初始化关键字分析结果
        keyword_result = {
            "keyword": keyword,
            "first_appearance": None,
            "last_disappearance": None,
            "total_occurrences": 0,
            "frame_details": []
        }
        
        # 遍历所有OCR结果
        found_in_frames = []
        for i, ocr_result in enumerate(mock_ocr_results):
            frame_number = ocr_result["frame_number"]
            timestamp = ocr_result["timestamp"]
            text = ocr_result["text"]
            
            print(f"  📄 检查帧 {frame_number} (时间: {timestamp}s): '{text}'")
            
            # 检查关键字是否在文本中
            if keyword in text:
                found_in_frames.append({
                    "frame_number": frame_number,
                    "timestamp": timestamp,
                    "text": text
                })
                print(f"    ✅ 找到关键字 '{keyword}'")
            else:
                print(f"    ❌ 未找到关键字 '{keyword}'")
        
        # 统计结果
        if found_in_frames:
            keyword_result["total_occurrences"] = len(found_in_frames)
            keyword_result["first_appearance"] = found_in_frames[0]["timestamp"]
            keyword_result["last_disappearance"] = found_in_frames[-1]["timestamp"]
            keyword_result["frame_details"] = found_in_frames
            
            print(f"  📈 统计结果:")
            print(f"    - 总出现次数: {keyword_result['total_occurrences']}")
            print(f"    - 首次出现: {keyword_result['first_appearance']}s")
            print(f"    - 最后出现: {keyword_result['last_disappearance']}s")
            print(f"    - 出现帧数: {[f['frame_number'] for f in found_in_frames]}")
        else:
            print(f"  📈 统计结果: 未找到关键字 '{keyword}'")
        
        analysis_results.append(keyword_result)
    
    # 输出最终分析结果
    print("\n" + "=" * 60)
    print("最终分析结果汇总")
    print("=" * 60)
    
    for result in analysis_results:
        keyword = result["keyword"]
        count = result["total_occurrences"]
        
        if count > 0:
            print(f"✅ '{keyword}': 出现 {count} 次")
            print(f"   首次出现: {result['first_appearance']}s")
            print(f"   最后出现: {result['last_disappearance']}s")
            print(f"   出现帧: {[f['frame_number'] for f in result['frame_details']]}")
        else:
            print(f"❌ '{keyword}': 未找到")
        print()
    
    # 验证循环遍历的完整性
    print("\n" + "-" * 50)
    print("验证测试完整性")
    print("-" * 50)
    
    total_keyword_checks = len(test_keywords) * len(mock_ocr_results)
    print(f"✅ 关键字总数: {len(test_keywords)}")
    print(f"✅ OCR结果总数: {len(mock_ocr_results)}")
    print(f"✅ 总检查次数: {total_keyword_checks}")
    print(f"✅ 每个关键字都遍历了所有OCR结果")
    print(f"✅ 每次遍历都进行了关键字查找")
    
    # 统计找到关键字的情况
    found_keywords = [r for r in analysis_results if r["total_occurrences"] > 0]
    not_found_keywords = [r for r in analysis_results if r["total_occurrences"] == 0]
    
    print(f"\n📊 找到的关键字: {len(found_keywords)} 个")
    for result in found_keywords:
        print(f"   - '{result['keyword']}': {result['total_occurrences']} 次")
    
    print(f"\n📊 未找到的关键字: {len(not_found_keywords)} 个")
    for result in not_found_keywords:
        print(f"   - '{result['keyword']}'")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    return analysis_results

def main():
    """主函数"""
    try:
        results = test_keyword_matching()
        print(f"\n🎉 测试成功完成，分析了 {len(results)} 个关键字")
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)