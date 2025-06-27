#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试关键词分析功能 - 使用真实数据库
"""

import asyncio
import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 简化的数据库连接
class SimpleDB:
    def __init__(self):
        self.conn = sqlite3.connect('video_analysis.db')
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        self.conn.close()

# 模拟关键词分析请求
class KeywordAnalysisRequest:
    def __init__(self, keywords, analysis_type="both"):
        self.keywords = keywords
        self.analysis_type = analysis_type

def analyze_keywords_manual(db, video_id, keywords):
    """手动实现关键词分析逻辑"""
    cursor = db.conn.cursor()
    
    # 获取视频帧和OCR结果
    cursor.execute("""
        SELECT vf.id as frame_id, vf.timestamp_ms, ocr.text_content, ocr.confidence
        FROM video_frames vf 
        JOIN ocr_results ocr ON vf.id = ocr.frame_id 
        WHERE vf.video_id = ? 
        ORDER BY vf.timestamp_ms
    """, (video_id,))
    
    frames_data = cursor.fetchall()
    
    if not frames_data:
        return {"message": "没有找到OCR数据", "video_id": video_id, "analyzed_keywords": 0, "analysis_results": []}
    
    analysis_results = []
    
    for keyword in keywords:
        keyword_analysis = {
            "keyword": keyword,
            "first_appearance_timestamp": None,
            "first_disappearance_timestamp": None,
            "total_occurrences": 0,
            "frame_occurrences": [],
            "pattern_analysis": {
                "continuous_periods": [],
                "gap_periods": []
            }
        }
        
        previous_found = False
        current_period_start = None
        
        for frame in frames_data:
            text_content = frame['text_content'] or ""
            found_in_frame = keyword.lower() in text_content.lower()
            
            if found_in_frame:
                keyword_analysis["total_occurrences"] += 1
                keyword_analysis["frame_occurrences"].append({
                    "frame_id": frame['frame_id'],
                    "timestamp_ms": frame['timestamp_ms'],
                    "confidence": float(frame['confidence']) if frame['confidence'] else 0.0
                })
                
                # 记录第一次出现
                if keyword_analysis["first_appearance_timestamp"] is None:
                    keyword_analysis["first_appearance_timestamp"] = frame['timestamp_ms']
                
                # 开始连续期间
                if not previous_found:
                    current_period_start = frame['timestamp_ms']
            
            else:
                # 关键词消失
                if previous_found:
                    # 记录第一次消失
                    if keyword_analysis["first_disappearance_timestamp"] is None:
                        keyword_analysis["first_disappearance_timestamp"] = frame['timestamp_ms']
                    
                    # 结束连续期间
                    if current_period_start is not None:
                        keyword_analysis["pattern_analysis"]["continuous_periods"].append({
                            "start_timestamp": current_period_start,
                            "end_timestamp": frame['timestamp_ms'],
                            "duration_ms": frame['timestamp_ms'] - current_period_start
                        })
                        current_period_start = None
            
            previous_found = found_in_frame
        
        # 处理最后一个连续期间
        if current_period_start is not None and frames_data:
            last_frame = frames_data[-1]
            keyword_analysis["pattern_analysis"]["continuous_periods"].append({
                "start_timestamp": current_period_start,
                "end_timestamp": last_frame['timestamp_ms'],
                "duration_ms": last_frame['timestamp_ms'] - current_period_start
            })
        
        analysis_results.append(keyword_analysis)
    
    return {
        "message": "关键词分析完成",
        "video_id": video_id,
        "analyzed_keywords": len(keywords),
        "analysis_results": analysis_results
    }

async def test_keyword_analysis():
    """测试关键词分析功能"""
    print("=== 关键词分析测试 ===")
    
    # 获取数据库连接
    db = SimpleDB()
    
    try:
        # 测试1: 分析"加载中"关键词
        print("\n测试1: 分析'加载中'关键词")
        result1 = analyze_keywords_manual(db, 1, ["加载中"])
        print(f"结果1: {result1}")
        
        # 测试2: 分析"string"关键词
        print("\n测试2: 分析'string'关键词")
        result2 = analyze_keywords_manual(db, 1, ["string"])
        print(f"结果2: {result2}")
        
        # 测试3: 分析多个关键词
        print("\n测试3: 分析多个关键词")
        result3 = analyze_keywords_manual(db, 1, ["加载中", "飞书", "string", "技术"])
        print(f"结果3: {result3}")
        
        # 分析结果
        print("\n=== 分析总结 ===")
        for i, result in enumerate([result1, result2, result3], 1):
            print(f"\n测试{i}结果分析:")
            if 'analysis_results' in result:
                for keyword_result in result['analysis_results']:
                    keyword = keyword_result['keyword']
                    occurrences = keyword_result['total_occurrences']
                    first_appear = keyword_result['first_appearance_timestamp']
                    print(f"  关键词'{keyword}': 出现{occurrences}次, 首次出现时间: {first_appear}ms")
            else:
                print(f"  结果格式异常: {result}")
                
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_keyword_analysis())