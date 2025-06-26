#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版数据库模型 - 使用SQLAlchemy
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, DECIMAL, TIMESTAMP, Enum, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import json

Base = declarative_base()


class ProcessStatus(enum.Enum):
    """处理状态枚举"""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class AnalysisStatus(enum.Enum):
    """分析状态枚举"""
    detected = "detected"
    confirmed = "confirmed"
    manual_adjusted = "manual_adjusted"


class ReportType(enum.Enum):
    """报告类型枚举"""
    timeline = "timeline"
    duration_chart = "duration_chart"
    comparison = "comparison"
    summary = "summary"


class Project(Base):
    """项目表"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    status = Column(String(20), default="active", comment="项目状态")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    videos = relationship("Video", back_populates="project", cascade="all, delete-orphan")


class Video(Base):
    """视频表"""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    stored_filename = Column(String(255), nullable=False, comment="存储文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    duration_ms = Column(BigInteger, comment="视频时长(毫秒)")
    fps = Column(DECIMAL(10, 2), comment="帧率")
    resolution = Column(String(20), comment="分辨率 如1920x1080")
    format = Column(String(10), comment="视频格式")
    upload_time = Column(TIMESTAMP, default=datetime.utcnow)
    process_status = Column(Enum(ProcessStatus), default=ProcessStatus.pending)
    
    # 关系
    project = relationship("Project", back_populates="videos")
    stage_configs = relationship("StageConfig", back_populates="video", cascade="all, delete-orphan")
    video_frames = relationship("VideoFrame", back_populates="video", cascade="all, delete-orphan")
    stage_analysis_results = relationship("StageAnalysisResult", back_populates="video", cascade="all, delete-orphan")
    visualization_reports = relationship("VisualizationReport", back_populates="video", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_project_status', 'project_id', 'process_status'),
    )


class StageConfig(Base):
    """阶段配置表"""
    __tablename__ = "stage_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    stage_name = Column(String(100), nullable=False, comment="阶段名称")
    stage_order = Column(Integer, nullable=False, comment="阶段顺序")
    keywords = Column(JSON, nullable=False, comment="关键词列表")
    start_rule = Column(JSON, comment="起始规则配置")
    end_rule = Column(JSON, comment="结束规则配置")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 关系
    video = relationship("Video", back_populates="stage_configs")
    stage_analysis_results = relationship("StageAnalysisResult", back_populates="stage_config", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_video_order', 'video_id', 'stage_order'),
    )


class VideoFrame(Base):
    """视频帧表"""
    __tablename__ = "video_frames"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    frame_number = Column(Integer, nullable=False, comment="帧序号")
    timestamp_ms = Column(BigInteger, nullable=False, comment="时间戳(毫秒)")
    frame_path = Column(String(500), nullable=False, comment="帧图片存储路径")
    file_size = Column(Integer, comment="帧文件大小")
    extracted_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 关系
    video = relationship("Video", back_populates="video_frames")
    ocr_results = relationship("OCRResult", back_populates="frame", cascade="all, delete-orphan")
    start_stage_results = relationship("StageAnalysisResult", foreign_keys="StageAnalysisResult.start_frame_id", back_populates="start_frame")
    end_stage_results = relationship("StageAnalysisResult", foreign_keys="StageAnalysisResult.end_frame_id", back_populates="end_frame")
    
    # 索引
    __table_args__ = (
        Index('idx_video_timestamp', 'video_id', 'timestamp_ms'),
        Index('idx_video_frame', 'video_id', 'frame_number'),
    )


class OCRResult(Base):
    """OCR识别结果表"""
    __tablename__ = "ocr_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    frame_id = Column(Integer, ForeignKey("video_frames.id", ondelete="CASCADE"), nullable=False)
    text_content = Column(Text, comment="识别的文本内容")
    confidence = Column(DECIMAL(5, 4), comment="识别置信度")
    bbox = Column(JSON, comment="文本框坐标信息")
    processed_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 关系
    frame = relationship("VideoFrame", back_populates="ocr_results")
    
    # 索引
    __table_args__ = (
        Index('idx_frame_confidence', 'frame_id', 'confidence'),
    )


class StageAnalysisResult(Base):
    """阶段分析结果表"""
    __tablename__ = "stage_analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    stage_config_id = Column(Integer, ForeignKey("stage_configs.id", ondelete="CASCADE"), nullable=False)
    stage_name = Column(String(100), nullable=False)
    start_timestamp_ms = Column(BigInteger, comment="开始时间戳")
    end_timestamp_ms = Column(BigInteger, comment="结束时间戳")
    duration_ms = Column(BigInteger, comment="耗时(毫秒)")
    start_frame_id = Column(Integer, ForeignKey("video_frames.id"), comment="开始帧ID")
    end_frame_id = Column(Integer, ForeignKey("video_frames.id"), comment="结束帧ID")
    matched_keywords = Column(JSON, comment="匹配到的关键词")
    confidence_score = Column(DECIMAL(5, 4), comment="匹配置信度")
    analysis_status = Column(Enum(AnalysisStatus), default=AnalysisStatus.detected)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 关系
    video = relationship("Video", back_populates="stage_analysis_results")
    stage_config = relationship("StageConfig", back_populates="stage_analysis_results")
    start_frame = relationship("VideoFrame", foreign_keys=[start_frame_id], back_populates="start_stage_results")
    end_frame = relationship("VideoFrame", foreign_keys=[end_frame_id], back_populates="end_stage_results")
    
    # 索引
    __table_args__ = (
        Index('idx_video_stage', 'video_id', 'stage_config_id'),
        Index('idx_timestamp_range', 'start_timestamp_ms', 'end_timestamp_ms'),
    )


class VisualizationReport(Base):
    """可视化报告表"""
    __tablename__ = "visualization_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(Enum(ReportType), nullable=False)
    chart_path = Column(String(500), comment="图表文件路径")
    chart_config = Column(JSON, comment="图表配置信息")
    generated_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 关系
    video = relationship("Video", back_populates="visualization_reports")
    
    # 索引
    __table_args__ = (
        Index('idx_video_type', 'video_id', 'report_type'),
    )


# 辅助函数
def json_to_dict(json_str: str) -> dict:
    """JSON字符串转字典"""
    if not json_str:
        return {}
    try:
        return json.loads(json_str) if isinstance(json_str, str) else json_str
    except (json.JSONDecodeError, TypeError):
        return {}


def dict_to_json(data: dict) -> str:
    """字典转JSON字符串"""
    if not data:
        return "{}"
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return "{}"