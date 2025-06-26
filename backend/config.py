#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置文件
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置类"""
    
    # 应用基础设置
    app_name: str = "视频耗时分析系统"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 数据库设置
    database_url: str = "sqlite:///./video_analysis.db"
    database_echo: bool = True  # 是否显示SQL语句
    
    # 存储设置
    storage_base_path: str = "./data"
    max_video_size: int = 500 * 1024 * 1024  # 500MB
    max_frame_size: int = 5 * 1024 * 1024    # 5MB
    
    # 视频处理设置
    frame_extract_fps: float = 1.0  # 每秒提取帧数
    frame_quality: int = 85         # JPEG质量
    supported_video_formats: list = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]
    
    # OCR设置
    ocr_language: str = "ch"  # 中文
    ocr_use_gpu: bool = False
    ocr_confidence_threshold: float = 0.7
    ocr_use_doc_orientation_classify: bool = False
    ocr_use_doc_unwarping: bool = False
    ocr_use_textline_orientation: bool = False
    
    # 分析设置
    default_keywords: list = ["加载中", "Loading", "请稍候", "Please wait"]
    keyword_match_confidence: float = 0.8
    stage_detection_confidence: float = 0.7
    
    # 可视化设置
    chart_width: int = 1200
    chart_height: int = 800
    chart_dpi: int = 300
    chart_format: str = "png"
    
    # 文件清理设置
    temp_file_retention_hours: int = 24
    frame_retention_days: int = 30
    video_archive_days: int = 90
    
    # API设置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    cors_origins: list = ["*"]
    
    # 日志设置
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    
    # 安全设置
    secret_key: str = "your-secret-key-here-change-in-production"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class VideoProcessingConfig:
    """视频处理配置"""
    
    # OpenCV设置
    OPENCV_BACKEND = "CAP_FFMPEG"
    
    # 帧提取设置
    FRAME_EXTRACT_SETTINGS = {
        "fps": 1.0,
        "quality": 85,
        "format": "jpg",
        "resize_width": None,  # 不调整大小
        "resize_height": None
    }
    
    # 视频分析设置
    ANALYSIS_SETTINGS = {
        "min_stage_duration_ms": 100,  # 最小阶段时长
        "max_stage_duration_ms": 60000,  # 最大阶段时长
        "overlap_tolerance_ms": 50,  # 重叠容忍度
        "confidence_threshold": 0.7
    }


class OCRConfig:
    """OCR配置"""
    
    # PaddleOCR设置 - 支持PP-OCRv5
    PADDLE_OCR_SETTINGS = {
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
        "lang": "ch",
        "device": "cpu",  # 或 "gpu"
        "show_log": False,
        # PP-OCRv5 模型配置
        "ocr_version": "PP-OCRv5",
        "det_model_name": "PP-OCRv5_server_det",
        "rec_model_name": "PP-OCRv5_server_rec",
        "cls_model_name": "PP-LCNet_x1_0_doc_ori"
    }
    
    # 文本处理设置
    TEXT_PROCESSING = {
        "min_confidence": 0.7,
        "min_text_length": 1,
        "max_text_length": 1000,
        "filter_special_chars": True,
        "normalize_whitespace": True
    }
    
    # 关键词匹配设置
    KEYWORD_MATCHING = {
        "case_sensitive": False,
        "partial_match": True,
        "fuzzy_match_threshold": 0.8,
        "use_regex": False
    }


class VisualizationConfig:
    """可视化配置"""
    
    # Matplotlib设置
    MATPLOTLIB_SETTINGS = {
        "figure_size": (12, 8),
        "dpi": 300,
        "style": "seaborn-v0_8",
        "font_family": "SimHei",  # 支持中文
        "font_size": 12
    }
    
    # Plotly设置
    PLOTLY_SETTINGS = {
        "width": 1200,
        "height": 800,
        "theme": "plotly_white",
        "font_family": "Arial, sans-serif",
        "font_size": 14
    }
    
    # 图表类型设置
    CHART_TYPES = {
        "timeline": {
            "type": "gantt",
            "color_scheme": "viridis",
            "show_duration": True
        },
        "duration_chart": {
            "type": "bar",
            "color_scheme": "blues",
            "show_values": True
        },
        "comparison": {
            "type": "line",
            "color_scheme": "category10",
            "show_markers": True
        },
        "summary": {
            "type": "pie",
            "color_scheme": "pastel",
            "show_percentages": True
        }
    }


class DatabaseConfig:
    """数据库配置"""
    
    # SQLite设置
    SQLITE_SETTINGS = {
        "check_same_thread": False,
        "timeout": 30,
        "isolation_level": None
    }
    
    # MySQL设置（如果使用MySQL）
    MYSQL_SETTINGS = {
        "charset": "utf8mb4",
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 3600
    }
    
    # 连接池设置
    CONNECTION_POOL = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600
    }


# 创建全局设置实例
settings = Settings()


def get_settings() -> Settings:
    """获取应用设置"""
    return settings


def get_database_url() -> str:
    """获取数据库URL"""
    return settings.database_url


def get_storage_path() -> Path:
    """获取存储路径"""
    return Path(settings.storage_base_path)


def create_directories():
    """创建必要的目录"""
    directories = [
        Path(settings.storage_base_path),
        Path(settings.storage_base_path) / "videos",
        Path(settings.storage_base_path) / "frames",
        Path(settings.storage_base_path) / "charts",
        Path(settings.storage_base_path) / "temp",
        Path(settings.storage_base_path) / "backups",
        Path("./logs")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # 测试配置
    print("应用配置:")
    print(f"应用名称: {settings.app_name}")
    print(f"版本: {settings.app_version}")
    print(f"数据库URL: {settings.database_url}")
    print(f"存储路径: {settings.storage_base_path}")
    print(f"OCR语言: {settings.ocr_language}")
    print(f"帧提取FPS: {settings.frame_extract_fps}")
    
    # 创建目录
    create_directories()
    print("\n目录创建完成")