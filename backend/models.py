from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json
from pydantic import validator


class ProcessStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisStatus(str, Enum):
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    MANUAL_ADJUSTED = "manual_adjusted"


class ReportType(str, Enum):
    TIMELINE = "timeline"
    DURATION_CHART = "duration_chart"
    COMPARISON = "comparison"
    SUMMARY = "summary"


class Project(SQLModel, table=True):
    __tablename__ = "projects"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="active", max_length=20)
    
    # 关系
    videos: List["Video"] = Relationship(back_populates="project")


class Video(SQLModel, table=True):
    __tablename__ = "videos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    original_filename: str = Field(max_length=255)
    stored_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int
    duration_ms: Optional[int] = None
    fps: Optional[float] = None
    resolution: Optional[str] = Field(default=None, max_length=20)
    format: Optional[str] = Field(default=None, max_length=10)
    upload_time: datetime = Field(default_factory=datetime.now)
    process_status: ProcessStatus = Field(default=ProcessStatus.PENDING)
    
    # 关系
    project: Optional[Project] = Relationship(back_populates="videos")
    stage_configs: List["StageConfig"] = Relationship(back_populates="video")
    video_frames: List["VideoFrame"] = Relationship(back_populates="video")
    stage_analysis_results: List["StageAnalysisResult"] = Relationship(back_populates="video")
    visualization_reports: List["VisualizationReport"] = Relationship(back_populates="video")


class StageConfig(SQLModel, table=True):
    __tablename__ = "stage_configs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="videos.id")
    stage_name: str = Field(max_length=100)
    stage_order: int
    keywords: str = Field(sa_column_kwargs={"type_": "JSON"})  # JSON字段
    start_rule: Optional[str] = Field(default=None, sa_column_kwargs={"type_": "JSON"})
    end_rule: Optional[str] = Field(default=None, sa_column_kwargs={"type_": "JSON"})
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 关系
    video: Optional[Video] = Relationship(back_populates="stage_configs")
    stage_analysis_results: List["StageAnalysisResult"] = Relationship(back_populates="stage_config")
    
    def set_keywords(self, keywords_dict: Dict[str, Any]):
        """设置关键词JSON数据"""
        self.keywords = json.dumps(keywords_dict, ensure_ascii=False)
    
    def get_keywords(self) -> Dict[str, Any]:
        """获取关键词JSON数据"""
        return json.loads(self.keywords) if self.keywords else {}
    
    def set_start_rule(self, rule_dict: Dict[str, Any]):
        """设置开始规则JSON数据"""
        self.start_rule = json.dumps(rule_dict, ensure_ascii=False)
    
    def get_start_rule(self) -> Dict[str, Any]:
        """获取开始规则JSON数据"""
        return json.loads(self.start_rule) if self.start_rule else {}
    
    def set_end_rule(self, rule_dict: Dict[str, Any]):
        """设置结束规则JSON数据"""
        self.end_rule = json.dumps(rule_dict, ensure_ascii=False)
    
    def get_end_rule(self) -> Dict[str, Any]:
        """获取结束规则JSON数据"""
        return json.loads(self.end_rule) if self.end_rule else {}


class VideoFrame(SQLModel, table=True):
    __tablename__ = "video_frames"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="videos.id")
    frame_number: int
    timestamp_ms: int
    frame_path: str = Field(max_length=500)
    file_size: Optional[int] = None
    extracted_at: datetime = Field(default_factory=datetime.now)
    
    # 关系
    video: Optional[Video] = Relationship(back_populates="video_frames")
    ocr_results: List["OCRResult"] = Relationship(back_populates="frame")
    start_analysis_results: List["StageAnalysisResult"] = Relationship(
        back_populates="start_frame",
        sa_relationship_kwargs={"foreign_keys": "[StageAnalysisResult.start_frame_id]"}
    )
    end_analysis_results: List["StageAnalysisResult"] = Relationship(
        back_populates="end_frame",
        sa_relationship_kwargs={"foreign_keys": "[StageAnalysisResult.end_frame_id]"}
    )


class OCRResult(SQLModel, table=True):
    __tablename__ = "ocr_results"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    frame_id: int = Field(foreign_key="video_frames.id")
    text_content: Optional[str] = None
    confidence: Optional[float] = None
    bbox: Optional[str] = Field(default=None, sa_column_kwargs={"type_": "JSON"})
    processed_at: datetime = Field(default_factory=datetime.now)
    
    # 关系
    frame: Optional[VideoFrame] = Relationship(back_populates="ocr_results")
    
    def set_bbox(self, bbox_dict: Dict[str, Any]):
        """设置边界框JSON数据"""
        self.bbox = json.dumps(bbox_dict, ensure_ascii=False)
    
    def get_bbox(self) -> Dict[str, Any]:
        """获取边界框JSON数据"""
        return json.loads(self.bbox) if self.bbox else {}


class StageAnalysisResult(SQLModel, table=True):
    __tablename__ = "stage_analysis_results"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="videos.id")
    stage_config_id: int = Field(foreign_key="stage_configs.id")
    stage_name: str = Field(max_length=100)
    start_timestamp_ms: Optional[int] = None
    end_timestamp_ms: Optional[int] = None
    duration_ms: Optional[int] = None
    start_frame_id: Optional[int] = Field(default=None, foreign_key="video_frames.id")
    end_frame_id: Optional[int] = Field(default=None, foreign_key="video_frames.id")
    matched_keywords: Optional[str] = Field(default=None, sa_column_kwargs={"type_": "JSON"})
    confidence_score: Optional[float] = None
    analysis_status: AnalysisStatus = Field(default=AnalysisStatus.DETECTED)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 关系
    video: Optional[Video] = Relationship(back_populates="stage_analysis_results")
    stage_config: Optional[StageConfig] = Relationship(back_populates="stage_analysis_results")
    start_frame: Optional[VideoFrame] = Relationship(
        back_populates="start_analysis_results",
        sa_relationship_kwargs={"foreign_keys": "[StageAnalysisResult.start_frame_id]"}
    )
    end_frame: Optional[VideoFrame] = Relationship(
        back_populates="end_analysis_results",
        sa_relationship_kwargs={"foreign_keys": "[StageAnalysisResult.end_frame_id]"}
    )
    
    def set_matched_keywords(self, keywords_list: List[str]):
        """设置匹配关键词JSON数据"""
        self.matched_keywords = json.dumps(keywords_list, ensure_ascii=False)
    
    def get_matched_keywords(self) -> List[str]:
        """获取匹配关键词JSON数据"""
        return json.loads(self.matched_keywords) if self.matched_keywords else []


class VisualizationReport(SQLModel, table=True):
    __tablename__ = "visualization_reports"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="videos.id")
    report_type: ReportType
    chart_path: Optional[str] = Field(default=None, max_length=500)
    chart_config: Optional[str] = Field(default=None, sa_column_kwargs={"type_": "JSON"})
    generated_at: datetime = Field(default_factory=datetime.now)
    
    # 关系
    video: Optional[Video] = Relationship(back_populates="visualization_reports")
    
    def set_chart_config(self, config_dict: Dict[str, Any]):
        """设置图表配置JSON数据"""
        self.chart_config = json.dumps(config_dict, ensure_ascii=False)
    
    def get_chart_config(self) -> Dict[str, Any]:
        """获取图表配置JSON数据"""
        return json.loads(self.chart_config) if self.chart_config else {}