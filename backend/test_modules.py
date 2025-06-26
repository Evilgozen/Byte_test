#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块化重构测试脚本
用于验证各个模块是否正确导入和初始化
"""

import sys
import os
from pathlib import Path

def test_module_imports():
    """测试模块导入"""
    print("=== 模块导入测试 ===")
    
    try:
        # 测试视频模块
        from video_module import video_manager, VideoResponse
        print("✓ 视频模块导入成功")
        print(f"  - VideoManager实例: {type(video_manager).__name__}")
        print(f"  - VideoResponse模型: {VideoResponse.__name__}")
    except Exception as e:
        print(f"✗ 视频模块导入失败: {e}")
        return False
    
    try:
        # 测试帧提取模块
        from frame_extraction_module import frame_extractor, FrameExtractionRequest, VideoFrameResponse
        print("✓ 帧提取模块导入成功")
        print(f"  - FrameExtractor实例: {type(frame_extractor).__name__}")
        print(f"  - FrameExtractionRequest模型: {FrameExtractionRequest.__name__}")
        print(f"  - VideoFrameResponse模型: {VideoFrameResponse.__name__}")
    except Exception as e:
        print(f"✗ 帧提取模块导入失败: {e}")
        return False
    
    try:
        # 测试OCR模块
        from ocr_module import ocr_processor, OCRProcessRequest, OCRResultResponse, KeywordAnalysisRequest
        print("✓ OCR模块导入成功")
        print(f"  - OCRProcessor实例: {type(ocr_processor).__name__}")
        print(f"  - OCRProcessRequest模型: {OCRProcessRequest.__name__}")
        print(f"  - OCRResultResponse模型: {OCRResultResponse.__name__}")
        print(f"  - KeywordAnalysisRequest模型: {KeywordAnalysisRequest.__name__}")
    except Exception as e:
        print(f"✗ OCR模块导入失败: {e}")
        return False
    
    return True

def test_main_app_import():
    """测试主应用导入"""
    print("\n=== 主应用导入测试 ===")
    
    try:
        # 测试主应用
        import main
        print("✓ 主应用导入成功")
        print(f"  - FastAPI应用: {type(main.app).__name__}")
        
        # 检查路由数量
        routes_count = len(main.app.routes)
        print(f"  - API路由数量: {routes_count}")
        
        return True
    except Exception as e:
        print(f"✗ 主应用导入失败: {e}")
        return False

def test_database_models():
    """测试数据库模型"""
    print("\n=== 数据库模型测试 ===")
    
    try:
        from models_simple import Base, Project, Video, StageConfig, VideoFrame, ProcessStatus, OCRResult
        print("✓ 数据库模型导入成功")
        print(f"  - 模型数量: 6个 (Project, Video, StageConfig, VideoFrame, ProcessStatus, OCRResult)")
        return True
    except Exception as e:
        print(f"✗ 数据库模型导入失败: {e}")
        return False

def check_directory_structure():
    """检查目录结构"""
    print("\n=== 目录结构检查 ===")
    
    required_files = [
        "main.py",
        "video_module.py", 
        "frame_extraction_module.py",
        "ocr_module.py",
        "models_simple.py"
    ]
    
    current_dir = Path(".")
    missing_files = []
    
    for file in required_files:
        file_path = current_dir / file
        if file_path.exists():
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 缺失")
            missing_files.append(file)
    
    return len(missing_files) == 0

def main():
    """主测试函数"""
    print("模块化重构验证测试")
    print("=" * 50)
    
    # 检查目录结构
    structure_ok = check_directory_structure()
    
    # 测试模块导入
    imports_ok = test_module_imports()
    
    # 测试数据库模型
    models_ok = test_database_models()
    
    # 测试主应用
    main_ok = test_main_app_import()
    
    # 总结
    print("\n=== 测试总结 ===")
    all_tests_passed = structure_ok and imports_ok and models_ok and main_ok
    
    if all_tests_passed:
        print("🎉 所有测试通过！模块化重构成功！")
        print("\n模块化架构说明:")
        print("- video_module.py: 负责视频上传、存储、查询等功能")
        print("- frame_extraction_module.py: 负责视频分帧、帧管理等功能")
        print("- ocr_module.py: 负责OCR识别、关键词分析等功能")
        print("- main.py: FastAPI应用入口，协调各模块工作")
    else:
        print("❌ 部分测试失败，请检查模块配置")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)