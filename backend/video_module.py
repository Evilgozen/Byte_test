# -*- coding: utf-8 -*-
"""
视频管理模块
负责视频上传、存储、信息管理等功能
"""

from fastapi import HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
from models_simple import Video, Project, ProcessStatus
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import shutil
import os


class VideoResponse(BaseModel):
    id: int
    project_id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    duration_ms: Optional[int]
    fps: Optional[float]
    resolution: Optional[str]
    format: Optional[str]
    upload_time: datetime
    process_status: str
    
    class Config:
        from_attributes = True


class VideoManager:
    """视频管理类"""
    
    def __init__(self):
        self.allowed_extensions = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]
        self.video_storage_path = "./data/videos"
        
        # 确保视频存储目录存在
        Path(self.video_storage_path).mkdir(parents=True, exist_ok=True)
    
    def validate_video_file(self, filename: str) -> bool:
        """验证视频文件格式"""
        file_extension = Path(filename).suffix.lower()
        return file_extension in self.allowed_extensions
    
    def generate_stored_filename(self, project_id: int, original_filename: str) -> str:
        """生成存储文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(original_filename).suffix.lower()
        return f"video_{project_id}_{timestamp}{file_extension}"
    
    def get_file_path(self, stored_filename: str) -> str:
        """获取文件完整路径"""
        return f"{self.video_storage_path}/{stored_filename}"
    
    async def upload_video(self, project_id: int, file: UploadFile, db: Session) -> dict:
        """上传视频文件"""
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查文件类型
        if not self.validate_video_file(file.filename):
            file_extension = Path(file.filename).suffix.lower()
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_extension}")
        
        # 生成存储文件名和路径
        stored_filename = self.generate_stored_filename(project_id, file.filename)
        file_path = self.get_file_path(stored_filename)
        
        # 保存文件
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = os.path.getsize(file_path)
            
            # 创建视频记录
            db_video = Video(
                project_id=project_id,
                original_filename=file.filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=file_size,
                format=Path(file.filename).suffix[1:],  # 去掉点号
                process_status=ProcessStatus.pending
            )
            
            db.add(db_video)
            db.commit()
            db.refresh(db_video)
            
            return {
                "message": "视频上传成功",
                "video_id": db_video.id,
                "filename": file.filename,
                "size": file_size
            }
            
        except Exception as e:
            # 如果保存失败，删除已上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    async def get_video(self, video_id: int, db: Session) -> Video:
        """获取指定视频"""
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        return video
    
    async def get_project_videos(self, project_id: int, db: Session) -> List[Video]:
        """获取项目的所有视频"""
        videos = db.query(Video).filter(Video.project_id == project_id).all()
        return videos
    
    def update_video_status(self, video_id: int, status: ProcessStatus, db: Session) -> None:
        """更新视频处理状态"""
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.process_status = status
            db.commit()
    
    def delete_video(self, video_id: int, db: Session) -> dict:
        """删除视频及其文件"""
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 删除视频文件
        if os.path.exists(video.file_path):
            try:
                os.remove(video.file_path)
            except Exception as e:
                print(f"删除视频文件失败: {video.file_path}, 错误: {e}")
        
        # 删除数据库记录
        db.delete(video)
        db.commit()
        
        return {
            "message": "视频删除成功",
            "video_id": video_id,
            "filename": video.original_filename
        }
    
    def get_video_info(self, video_id: int, db: Session) -> dict:
        """获取视频详细信息"""
        video = self.get_video(video_id, db)
        
        # 检查文件是否存在
        file_exists = os.path.exists(video.file_path)
        
        return {
            "id": video.id,
            "project_id": video.project_id,
            "original_filename": video.original_filename,
            "stored_filename": video.stored_filename,
            "file_path": video.file_path,
            "file_size": video.file_size,
            "duration_ms": video.duration_ms,
            "fps": video.fps,
            "resolution": video.resolution,
            "format": video.format,
            "upload_time": video.upload_time,
            "process_status": video.process_status.value,
            "file_exists": file_exists
        }


# 创建全局视频管理器实例
video_manager = VideoManager()