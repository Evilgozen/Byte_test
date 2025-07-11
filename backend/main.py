#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的FastAPI应用 - 使用模块化架构
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models_simple import Base, Project, Video, StageConfig, VideoFrame, ProcessStatus, OCRResult
from pathlib import Path
import json
import os
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# 导入模块化组件
from video_module import video_manager, VideoResponse
from frame_extraction_module import frame_extractor, FrameExtractionRequest, VideoFrameResponse
from ocr_module import ocr_processor, OCRProcessRequest, OCRResultResponse, EnhancedOCRResultResponse, KeywordAnalysisRequest
from keyword_pattern_module import keyword_pattern_analyzer, KeywordPatternRequest, StagePatternRequest

# 数据库配置
DATABASE_URL = "sqlite:///./video_analysis.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="视频耗时分析系统",
    description="用于分析视频加载各阶段耗时的系统",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory="data"), name="static")

# 依赖注入：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic模型
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# VideoResponse 已在 video_module 中定义

class StageConfigCreate(BaseModel):
    video_id: int
    stage_name: str
    stage_order: int
    keywords: List[str]
    start_rule: Optional[dict] = None
    end_rule: Optional[dict] = None

class StageConfigResponse(BaseModel):
    id: int
    video_id: int
    stage_name: str
    stage_order: int
    keywords: List[str]
    start_rule: Optional[dict]
    end_rule: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 以下模型已在各自模块中定义：
# - VideoFrameResponse 在 frame_extraction_module 中
# - FrameExtractionRequest 在 frame_extraction_module 中  
# - OCRResultResponse 在 ocr_module 中
# - OCRProcessRequest 在 ocr_module 中
# - KeywordAnalysisRequest 在 ocr_module 中
    
# KeywordAnalysisResponse 也在 ocr_module 中定义

class FrameInfo(BaseModel):
    """帧信息模型"""
    frame_number: int
    timestamp_ms: int
    file_size: int

class FrameExtractionResponse(BaseModel):
    """视频分帧响应模型"""
    message: str
    video_id: int
    total_frames: int
    frames: List[FrameInfo]
    
    class Config:
        from_attributes = True

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 确保数据目录存在
    directories = [
        "./data",
        "./data/videos",
        "./data/frames",
        "./data/charts",
        "./data/temp",
        "./data/backups",
        "./data/ocr_results"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ 视频耗时分析系统启动完成")
    print("✓ 模块化架构已加载：视频模块、帧提取模块、OCR模块")

# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "视频耗时分析系统",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

# 项目管理
@app.post("/projects/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """创建项目"""
    db_project = Project(
        name=project.name,
        description=project.description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[ProjectResponse])
async def get_projects(db: Session = Depends(get_db)):
    """获取所有项目"""
    projects = db.query(Project).all()
    return projects

@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取指定项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project

# 视频管理
@app.post("/videos/upload/{project_id}", response_model=VideoResponse)
async def upload_video(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传视频"""
    return await video_manager.upload_video(project_id, file, db)

@app.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """获取指定视频"""
    return await video_manager.get_video(video_id, db)

@app.get("/projects/{project_id}/videos/", response_model=List[VideoResponse])
async def get_project_videos(project_id: int, db: Session = Depends(get_db)):
    """获取项目的所有视频"""
    return await video_manager.get_project_videos(project_id, db)

# 阶段配置管理
@app.post("/stage-configs/", response_model=StageConfigResponse)
async def create_stage_config(config: StageConfigCreate, db: Session = Depends(get_db)):
    """创建阶段配置"""
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == config.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    db_config = StageConfig(
        video_id=config.video_id,
        stage_name=config.stage_name,
        stage_order=config.stage_order,
        keywords=json.dumps(config.keywords, ensure_ascii=False),
        start_rule=json.dumps(config.start_rule, ensure_ascii=False) if config.start_rule else None,
        end_rule=json.dumps(config.end_rule, ensure_ascii=False) if config.end_rule else None
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    # 转换JSON字段为Python对象
    response_config = StageConfigResponse(
        id=db_config.id,
        video_id=db_config.video_id,
        stage_name=db_config.stage_name,
        stage_order=db_config.stage_order,
        keywords=json.loads(db_config.keywords),
        start_rule=json.loads(db_config.start_rule) if db_config.start_rule else None,
        end_rule=json.loads(db_config.end_rule) if db_config.end_rule else None,
        created_at=db_config.created_at
    )
    
    return response_config

@app.get("/videos/{video_id}/stage-configs/", response_model=List[StageConfigResponse])
async def get_video_stage_configs(video_id: int, db: Session = Depends(get_db)):
    """获取视频的所有阶段配置"""
    configs = db.query(StageConfig).filter(StageConfig.video_id == video_id).order_by(StageConfig.stage_order).all()
    
    response_configs = []
    for config in configs:
        response_config = StageConfigResponse(
            id=config.id,
            video_id=config.video_id,
            stage_name=config.stage_name,
            stage_order=config.stage_order,
            keywords=json.loads(config.keywords),
            start_rule=json.loads(config.start_rule) if config.start_rule else None,
            end_rule=json.loads(config.end_rule) if config.end_rule else None,
            created_at=config.created_at
        )
        response_configs.append(response_config)
    
    return response_configs

@app.delete("/stage-configs/{config_id}")
async def delete_stage_config(config_id: int, db: Session = Depends(get_db)):
    """删除阶段配置"""
    # 查找阶段配置
    config = db.query(StageConfig).filter(StageConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="阶段配置不存在")
    
    # 删除相关的分析结果（由于设置了CASCADE，会自动删除）
    db.delete(config)
    db.commit()
    
    return {"message": "阶段配置删除成功", "config_id": config_id}

@app.delete("/videos/{video_id}/stage-configs/")
async def delete_all_video_stage_configs(video_id: int, db: Session = Depends(get_db)):
    """删除视频的所有阶段配置"""
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 删除该视频的所有阶段配置
    deleted_count = db.query(StageConfig).filter(StageConfig.video_id == video_id).delete()
    db.commit()
    
    return {
        "message": f"成功删除视频 {video_id} 的所有阶段配置",
        "video_id": video_id,
        "deleted_count": deleted_count
    }

# 系统信息
@app.get("/system/info")
async def get_system_info(db: Session = Depends(get_db)):
    """获取系统信息"""
    project_count = db.query(Project).count()
    video_count = db.query(Video).count()
    config_count = db.query(StageConfig).count()
    
    # 存储信息
    storage_info = {}
    storage_dirs = [
        "./data/videos",
        "./data/frames",
        "./data/charts",
        "./data/temp",
        "./data/backups"
    ]
    
    for dir_path in storage_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            file_count = len(list(path.glob("*")))
            storage_info[dir_path] = file_count
        else:
            storage_info[dir_path] = 0
    
    return {
        "database": {
            "projects": project_count,
            "videos": video_count,
            "stage_configs": config_count
        },
        "storage": storage_info,
        "system": {
            "status": "running",
            "version": "1.0.0"
        }
    }

# 视频分帧处理函数已移至 frame_extraction_module

# OCR处理函数和关键词分析函数已移至 ocr_module

# 视频分帧API
@app.post("/videos/{video_id}/extract-frames", response_model=FrameExtractionResponse)
async def extract_frames(video_id: int, request: FrameExtractionRequest, db: Session = Depends(get_db)):
    """提取视频帧"""
    return await frame_extractor.extract_frames_from_video(video_id, request, db)

# 获取视频帧列表
@app.get("/videos/{video_id}/frames", response_model=List[VideoFrameResponse])
async def get_video_frames(video_id: int, db: Session = Depends(get_db)):
    """获取视频的所有帧"""
    return await frame_extractor.get_video_frames(video_id, db)

# 获取单个视频帧信息
@app.get("/frames/{frame_id}", response_model=VideoFrameResponse)
async def get_frame(frame_id: int, db: Session = Depends(get_db)):
    """获取指定帧信息"""
    frame = db.query(VideoFrame).filter(VideoFrame.id == frame_id).first()
    if not frame:
        raise HTTPException(status_code=404, detail="帧不存在")
    return frame

# 查看帧图片
@app.get("/frames/{frame_id}/image")
async def get_frame_image(frame_id: int, db: Session = Depends(get_db)):
    """获取帧图片文件"""
    frame = db.query(VideoFrame).filter(VideoFrame.id == frame_id).first()
    if not frame:
        raise HTTPException(status_code=404, detail="帧不存在")
    
    # 检查图片文件是否存在
    if not os.path.exists(frame.frame_path):
        raise HTTPException(status_code=404, detail="帧图片文件不存在")
    
    return FileResponse(
        path=frame.frame_path,
        media_type="image/jpeg",
        filename=f"frame_{frame.frame_number}_{frame.timestamp_ms}ms.jpg"
    )

# 删除视频帧
@app.delete("/videos/{video_id}/frames")
async def delete_video_frames(video_id: int, db: Session = Depends(get_db)):
    """删除视频的所有帧"""
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 获取所有帧
    frames = db.query(VideoFrame).filter(VideoFrame.video_id == video_id).all()
    
    # 删除帧文件
    deleted_files = 0
    for frame in frames:
        if os.path.exists(frame.frame_path):
            try:
                os.remove(frame.frame_path)
                deleted_files += 1
            except Exception as e:
                print(f"删除帧文件失败: {frame.frame_path}, 错误: {e}")
    
    # 删除数据库记录
    db.query(VideoFrame).filter(VideoFrame.video_id == video_id).delete()
    db.commit()
    
    # 删除帧目录（如果为空）
    frames_dir = Path(f"./data/frames/video_{video_id}")
    if frames_dir.exists() and not any(frames_dir.iterdir()):
        frames_dir.rmdir()
    
    return {
        "message": "视频帧删除完成",
        "video_id": video_id,
        "deleted_frames": len(frames),
        "deleted_files": deleted_files
    }

# OCR处理API
@app.post("/videos/{video_id}/process-ocr")
async def process_video_ocr(video_id: int, request: OCRProcessRequest, db: Session = Depends(get_db)):
    """对视频的所有帧进行OCR处理"""
    return await ocr_processor.process_video_ocr(video_id, request, db)

# 获取OCR结果API
@app.get("/videos/{video_id}/ocr-results", response_model=List[OCRResultResponse])
async def get_video_ocr_results(video_id: int, db: Session = Depends(get_db)):
    """获取视频的所有OCR结果"""
    return ocr_processor.get_video_ocr_results(video_id, db)

# 获取增强的OCR结果API (PP-OCRv5)
@app.get("/videos/{video_id}/enhanced-ocr-results", response_model=List[EnhancedOCRResultResponse])
async def get_enhanced_ocr_results(video_id: int, db: Session = Depends(get_db)):
    """获取视频的增强OCR结果（PP-OCRv5格式）"""
    return ocr_processor.get_enhanced_ocr_results(video_id)

# 关键词分析API
@app.post("/videos/{video_id}/analyze-keywords")
async def analyze_video_keywords(video_id: int, request: KeywordAnalysisRequest, db: Session = Depends(get_db)):
    """分析视频中关键词的出现和消失模式"""
    return await ocr_processor.analyze_video_keywords(video_id, request, db)

# 获取单个帧的OCR结果
@app.get("/frames/{frame_id}/ocr-result", response_model=OCRResultResponse)
async def get_frame_ocr_result(frame_id: int, db: Session = Depends(get_db)):
    """获取指定帧的OCR结果"""
    return ocr_processor.get_frame_ocr_result(frame_id, db)

# 基于stage_configs的关键词分析API
@app.post("/videos/{video_id}/analyze-stage-keywords")
async def analyze_stage_keywords(video_id: int, db: Session = Depends(get_db)):
    """基于stage_configs分析关键词模式"""
    return await ocr_processor.analyze_stage_keywords(video_id, db)

# 删除OCR结果API
@app.delete("/videos/{video_id}/ocr-results")
async def delete_video_ocr_results(video_id: int, db: Session = Depends(get_db)):
    """删除视频的所有OCR结果（数据库记录和JSON文件）"""
    return ocr_processor.delete_video_ocr_results(video_id, db)

# 获取OCR存储信息API
@app.get("/videos/{video_id}/ocr-storage-info")
async def get_ocr_storage_info(video_id: int, db: Session = Depends(get_db)):
    """获取OCR结果的存储信息"""
    return ocr_processor.get_ocr_storage_info(video_id, db)

# 查看OCR结果API
@app.get("/videos/{video_id}/ocr-results/view")
async def view_video_ocr_results(video_id: int, db: Session = Depends(get_db)):
    """查看视频的OCR结果（包含数据库和JSON文件信息）"""
    return ocr_processor.view_video_ocr_results(video_id, db)

# 获取视频OCR图片列表API
@app.get("/videos/{video_id}/ocr-images")
async def get_video_ocr_images(video_id: int):
    """获取视频的所有OCR处理后图片列表"""
    return ocr_processor.get_video_ocr_images(video_id)

# 查看指定帧的OCR图片API
@app.get("/videos/{video_id}/frames/{frame_id}/ocr-image")
async def get_frame_ocr_image(video_id: int, frame_id: int):
    """获取指定帧的OCR处理后图片"""
    image_path = ocr_processor.get_frame_ocr_image_path(video_id, frame_id)
    return FileResponse(
        path=image_path,
        media_type="image/jpeg",
        filename=f"video_{video_id}_frame_{frame_id}_ocr.jpg"
    )

# 删除视频所有OCR图片API
@app.delete("/videos/{video_id}/ocr-images")
async def delete_video_ocr_images(video_id: int):
    """删除视频的所有OCR处理后图片"""
    return ocr_processor.delete_video_ocr_images(video_id)

# 删除指定帧的OCR图片API
@app.delete("/videos/{video_id}/frames/{frame_id}/ocr-image")
async def delete_frame_ocr_image(video_id: int, frame_id: int, db: Session = Depends(get_db)):
    """删除指定帧的OCR处理后图片"""
    try:
        success = ocr_processor.delete_frame_ocr_image(video_id, frame_id)
        if success:
            return {"message": f"帧 {frame_id} 的OCR图片删除成功"}
        else:
            raise HTTPException(status_code=404, detail="OCR图片不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除OCR图片失败: {str(e)}")

@app.get("/videos/{video_id}/frames/{frame_id}/raw-ocr-result")
async def get_raw_ocr_result(video_id: str, frame_id: str):
    """获取指定帧的原始OCR结果"""
    try:
        # 使用新的文件名格式
        frame_id_padded = f"{int(frame_id):06d}"
        raw_result_path = Path(f"./data/ocr_results/video_{video_id}/frame_{frame_id_padded}_333ms_ocr_res.json")
        
        if not raw_result_path.exists():
            raise HTTPException(status_code=404, detail="原始OCR结果文件不存在")
        
        with open(raw_result_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        return {
            "success": True,
            "data": raw_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取原始OCR结果失败: {str(e)}")

# 关键词模式匹配API
@app.post("/videos/{video_id}/analyze-keyword-pattern")
async def analyze_keyword_pattern(video_id: int, request: KeywordPatternRequest, db: Session = Depends(get_db)):
    """分析视频中关键词的模式，返回第一次出现和消失的时间戳"""
    return keyword_pattern_analyzer.analyze_keyword_pattern(video_id, request, db)

@app.post("/videos/{video_id}/analyze-stage-pattern")
async def analyze_stage_pattern(video_id: int, request: StagePatternRequest, db: Session = Depends(get_db)):
    """基于阶段配置分析关键词模式，返回每个阶段的时间戳信息"""
    return keyword_pattern_analyzer.analyze_stage_pattern(video_id, request, db)

@app.get("/videos/{video_id}/stage-pattern-summary")
async def get_stage_pattern_summary(video_id: int, db: Session = Depends(get_db)):
    """获取视频所有阶段的关键词模式摘要"""
    request = StagePatternRequest(confidence_threshold=0.0, include_pattern_details=False)
    result = keyword_pattern_analyzer.analyze_stage_pattern(video_id, request, db)
    
    # 返回简化的摘要信息
    summary = {
        "video_id": video_id,
        "total_stages": result["total_stages"],
        "analysis_timestamp": result["analysis_timestamp"],
        "stage_summaries": []
    }
    
    for stage in result["stage_results"]:
        stage_summary = {
            "stage_id": stage["stage_id"],
            "stage_name": stage["stage_name"],
            "stage_order": stage["stage_order"],
            "keywords": stage["keywords"],
            "stage_start_timestamp_ms": stage["stage_start_timestamp_ms"],
            "stage_end_timestamp_ms": stage["stage_end_timestamp_ms"],
            "stage_duration_ms": stage["stage_duration_ms"],
            "keywords_found": stage["pattern_summary"]["keywords_found"],
            "total_occurrences": stage["pattern_summary"]["total_occurrences"]
        }
        summary["stage_summaries"].append(stage_summary)
    
    summary["overall_summary"] = result["overall_summary"]
    return summary

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)