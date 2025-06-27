#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys

def check_ocr_data():
    """检查数据库中的OCR数据"""
    try:
        # 连接到正确的数据库文件
        conn = sqlite3.connect('video_analysis.db')
        print(f"成功连接到数据库: video_analysis.db")
        cursor = conn.cursor()
        
        # 检查所有表
        print("=== 数据库中的所有表 ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"表名: {table[0]}")
        
        # 检查OCR结果表结构
        print("\n=== OCR结果表结构 ===")
        cursor.execute("PRAGMA table_info(ocr_results)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"列: {col[1]}, 类型: {col[2]}")
        
        # 检查video_id=1的OCR结果
        print("\n=== Video ID=1 的OCR结果 ===")
        cursor.execute("""
            SELECT vf.id as frame_id, vf.timestamp_ms, ocr.text_content 
            FROM video_frames vf 
            JOIN ocr_results ocr ON vf.id = ocr.frame_id 
            WHERE vf.video_id = 1 
            ORDER BY vf.timestamp_ms 
            LIMIT 10
        """)
        results = cursor.fetchall()
        
        if results:
            print(f"找到 {len(results)} 条OCR结果:")
            for i, (frame_id, timestamp, text) in enumerate(results):
                print(f"{i+1}. Frame {frame_id} ({timestamp}ms): {text[:100]}...")
        else:
            print("未找到video_id=1的OCR结果")
        
        # 检查包含"加载中"的结果
        print("\n=== 包含'加载中'的OCR结果 ===")
        cursor.execute("""
            SELECT vf.id as frame_id, vf.video_id, vf.timestamp_ms, ocr.text_content 
            FROM video_frames vf 
            JOIN ocr_results ocr ON vf.id = ocr.frame_id 
            WHERE ocr.text_content LIKE '%加载中%' 
            LIMIT 10
        """)
        loading_results = cursor.fetchall()
        
        if loading_results:
            print(f"找到 {len(loading_results)} 条包含'加载中'的结果:")
            for frame_id, video_id, timestamp, text in loading_results:
                print(f"Video {video_id}, Frame {frame_id} ({timestamp}ms): {text[:100]}...")
        else:
            print("未找到包含'加载中'的OCR结果")
        
        # 检查包含"string"的结果
        print("\n=== 包含'string'的OCR结果 ===")
        cursor.execute("""
            SELECT vf.id as frame_id, vf.video_id, vf.timestamp_ms, ocr.text_content 
            FROM video_frames vf 
            JOIN ocr_results ocr ON vf.id = ocr.frame_id 
            WHERE ocr.text_content LIKE '%string%' 
            LIMIT 10
        """)
        string_results = cursor.fetchall()
        
        if string_results:
            print(f"找到 {len(string_results)} 条包含'string'的结果:")
            for frame_id, video_id, timestamp, text in string_results:
                print(f"Video {video_id}, Frame {frame_id} ({timestamp}ms): {text[:100]}...")
        else:
            print("未找到包含'string'的OCR结果")
        
        # 统计总数
        print("\n=== 统计信息 ===")
        cursor.execute("SELECT COUNT(*) FROM ocr_results")
        total_ocr = cursor.fetchone()[0]
        print(f"OCR结果总数: {total_ocr}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM video_frames vf 
            JOIN ocr_results ocr ON vf.id = ocr.frame_id 
            WHERE vf.video_id = 1
        """)
        video1_ocr = cursor.fetchone()[0]
        print(f"Video ID=1 的OCR结果数: {video1_ocr}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查数据库时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_ocr_data()