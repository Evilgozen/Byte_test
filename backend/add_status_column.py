#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加projects表的status列
"""

import sqlite3
import os

def add_status_column():
    """添加status列到projects表"""
    db_path = "./video_analysis.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查status列是否已存在
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'status' in columns:
            print("status列已存在，无需添加")
            return
        
        # 添加status列
        cursor.execute("ALTER TABLE projects ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
        
        # 更新现有记录的status值
        cursor.execute("UPDATE projects SET status = 'active' WHERE status IS NULL")
        
        # 提交更改
        conn.commit()
        print("✓ 成功添加status列到projects表")
        
        # 验证添加结果
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()
        print("\n当前projects表结构:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
            
    except Exception as e:
        print(f"添加status列失败: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_status_column()