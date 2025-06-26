#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版数据库初始化脚本
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_simple import Base, Project, Video, StageConfig, ProcessStatus
import json
from datetime import datetime


def create_directories():
    """创建必要的目录"""
    directories = [
        "./data",
        "./data/videos",
        "./data/frames",
        "./data/charts",
        "./data/temp",
        "./data/backups",
        "./logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {directory}")


def init_database():
    """初始化数据库"""
    # 创建数据库引擎
    database_url = "sqlite:///./video_analysis.db"
    engine = create_engine(database_url, echo=True)
    
    # 创建所有表
    print("正在创建数据库表...")
    Base.metadata.create_all(engine)
    print("✓ 数据库表创建完成")
    
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # 创建示例项目
        if session.query(Project).count() == 0:
            print("正在创建示例数据...")
            
            # 创建示例项目
            project = Project(
                name="视频加载时间分析项目",
                description="用于分析视频加载各阶段耗时的项目"
            )
            session.add(project)
            session.commit()
            
            print(f"✓ 创建示例项目: {project.name} (ID: {project.id})")
            
            # 创建示例阶段配置模板
            stage_templates = [
                {
                    "stage_name": "初始化阶段",
                    "stage_order": 1,
                    "keywords": ["初始化", "Initializing", "Starting"],
                    "start_rule": {
                        "type": "keyword_match",
                        "confidence_threshold": 0.8
                    },
                    "end_rule": {
                        "type": "keyword_disappear",
                        "timeout_ms": 5000
                    }
                },
                {
                    "stage_name": "加载阶段",
                    "stage_order": 2,
                    "keywords": ["加载中", "Loading", "请稍候", "Please wait"],
                    "start_rule": {
                        "type": "keyword_match",
                        "confidence_threshold": 0.7
                    },
                    "end_rule": {
                        "type": "keyword_disappear",
                        "timeout_ms": 3000
                    }
                },
                {
                    "stage_name": "完成阶段",
                    "stage_order": 3,
                    "keywords": ["完成", "Complete", "Done", "Success"],
                    "start_rule": {
                        "type": "keyword_match",
                        "confidence_threshold": 0.8
                    },
                    "end_rule": {
                        "type": "video_end",
                        "timeout_ms": 1000
                    }
                }
            ]
            
            print("阶段配置模板:")
            for template in stage_templates:
                print(f"  - {template['stage_name']}: {template['keywords']}")
        
        else:
            print("✓ 数据库已包含数据，跳过示例数据创建")
            
    except Exception as e:
        print(f"❌ 创建示例数据时出错: {e}")
        session.rollback()
    finally:
        session.close()
    
    return engine


def print_database_info():
    """打印数据库信息"""
    database_url = "sqlite:///./video_analysis.db"
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        project_count = session.query(Project).count()
        video_count = session.query(Video).count()
        
        print("\n=== 数据库信息 ===")
        print(f"数据库文件: video_analysis.db")
        print(f"项目数量: {project_count}")
        print(f"视频数量: {video_count}")
        
        if project_count > 0:
            projects = session.query(Project).all()
            print("\n项目列表:")
            for project in projects:
                print(f"  - ID: {project.id}, 名称: {project.name}")
                print(f"    描述: {project.description}")
                print(f"    创建时间: {project.created_at}")
                
    except Exception as e:
        print(f"❌ 获取数据库信息时出错: {e}")
    finally:
        session.close()


def print_storage_info():
    """打印存储信息"""
    print("\n=== 存储信息 ===")
    storage_dirs = [
        "./data/videos",
        "./data/frames", 
        "./data/charts",
        "./data/temp",
        "./data/backups"
    ]
    
    for dir_path in storage_dirs:
        path = Path(dir_path)
        if path.exists():
            file_count = len(list(path.glob("*"))) if path.is_dir() else 0
            print(f"  - {dir_path}: {file_count} 个文件")
        else:
            print(f"  - {dir_path}: 目录不存在")


def main():
    """主函数"""
    print("=== 视频耗时分析系统 - 数据库初始化 ===")
    print("正在初始化数据库和存储系统...\n")
    
    try:
        # 创建目录
        print("1. 创建存储目录")
        create_directories()
        
        # 初始化数据库
        print("\n2. 初始化数据库")
        engine = init_database()
        
        # 打印信息
        print_database_info()
        print_storage_info()
        
        print("\n=== 初始化完成 ===")
        print("\n接下来可以:")
        print("1. 启动FastAPI服务: python main.py")
        print("2. 或者运行: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("3. 访问API文档: http://localhost:8000/docs")
        print("4. 上传视频并配置分析阶段")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()