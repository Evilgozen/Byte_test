# -*- coding: utf-8 -*-
"""
OpenCV视频分帧模块
负责视频帧提取、存储和管理功能
"""

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from models_simple import Video, VideoFrame, ProcessStatus
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import cv2
import os


class FrameExtractionRequest(BaseModel):
    fps: Optional[float] = 3.0  # 每秒提取帧数
    quality: Optional[int] = 85  # JPEG质量
    max_frames: Optional[int] = None  # 最大帧数限制


class VideoFrameResponse(BaseModel):
    id: int
    video_id: int
    frame_number: int
    timestamp_ms: int
    frame_path: str
    file_size: Optional[int]
    extracted_at: datetime
    
    class Config:
        from_attributes = True


class FrameExtractor:
    """视频帧提取器"""
    
    def __init__(self):
        self.frames_storage_path = "./data/frames"
        
        # 确保帧存储目录存在
        Path(self.frames_storage_path).mkdir(parents=True, exist_ok=True)
    
    def create_frame_directory(self, video_id: int) -> Path:
        """为特定视频创建帧目录"""
        frame_dir = Path(f"{self.frames_storage_path}/video_{video_id}")
        frame_dir.mkdir(parents=True, exist_ok=True)
        return frame_dir
    
    def extract_video_frames(self, video_path: str, video_id: int, fps: float = 1.0, quality: int = 85, max_frames: int = None) -> List[dict]:
        """提取视频帧"""
        if not os.path.exists(video_path):
            raise ValueError(f"视频文件不存在: {video_path}")
        
        # 创建帧存储目录
        frames_dir = self.create_frame_directory(video_id)
        
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        try:
            # 获取视频信息
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration_ms = int((total_frames / video_fps) * 1000) if video_fps > 0 else 0
            
            # 计算帧间隔
            frame_interval = int(video_fps / fps) if fps > 0 else 1
            
            extracted_frames = []
            frame_count = 0
            saved_frame_number = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 按间隔提取帧
                if frame_count % frame_interval == 0:
                    # 计算时间戳
                    timestamp_ms = int((frame_count / video_fps) * 1000) if video_fps > 0 else frame_count * 1000
                    
                    # 生成帧文件名
                    frame_filename = f"frame_{saved_frame_number:06d}_{timestamp_ms}ms.jpg"
                    frame_path = frames_dir / frame_filename
                    
                    # 保存帧图片
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
                    success = cv2.imwrite(str(frame_path), frame, encode_params)
                    
                    if success:
                        file_size = os.path.getsize(frame_path)
                        
                        frame_info = {
                            "frame_number": saved_frame_number,
                            "timestamp_ms": timestamp_ms,
                            "frame_path": str(frame_path),
                            "file_size": file_size
                        }
                        extracted_frames.append(frame_info)
                        saved_frame_number += 1
                        
                        # 检查最大帧数限制
                        if max_frames and saved_frame_number >= max_frames:
                            break
                
                frame_count += 1
            
            return extracted_frames
            
        finally:
            cap.release()
    
    async def extract_frames_from_video(self, video_id: int, request: FrameExtractionRequest, db: Session) -> dict:
        """从视频提取帧并保存到数据库"""
        # 检查视频是否存在
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 检查视频文件是否存在
        if not os.path.exists(video.file_path):
            raise HTTPException(status_code=404, detail="视频文件不存在")
        
        try:
            # 更新视频状态为处理中
            video.process_status = ProcessStatus.processing
            db.commit()
            
            # 提取视频帧
            extracted_frames = self.extract_video_frames(
                video.file_path,
                video_id,
                request.fps,
                request.quality,
                request.max_frames
            )
            
            # 保存帧信息到数据库
            db_frames = []
            for frame_info in extracted_frames:
                db_frame = VideoFrame(
                    video_id=video_id,
                    frame_number=frame_info["frame_number"],
                    timestamp_ms=frame_info["timestamp_ms"],
                    frame_path=frame_info["frame_path"],
                    file_size=frame_info["file_size"]
                )
                db.add(db_frame)
                db_frames.append(db_frame)
            
            # 更新视频状态为完成
            video.process_status = ProcessStatus.completed
            db.commit()
            
            return {
                "message": "视频分帧完成",
                "video_id": video_id,
                "total_frames": len(extracted_frames),
                "frames": [{
                    "frame_number": frame["frame_number"],
                    "timestamp_ms": frame["timestamp_ms"],
                    "file_size": frame["file_size"]
                } for frame in extracted_frames]
            }
            
        except Exception as e:
            # 更新视频状态为失败
            video.process_status = ProcessStatus.failed
            db.commit()
            raise HTTPException(status_code=500, detail=f"视频分帧失败: {str(e)}")
    
    async def get_video_frames(self, video_id: int, db: Session) -> List[VideoFrame]:
        """获取视频的所有帧"""
        # 检查视频是否存在
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 获取视频帧
        frames = db.query(VideoFrame).filter(VideoFrame.video_id == video_id).order_by(VideoFrame.frame_number).all()
        return frames
    
    def get_frame(self, frame_id: int, db: Session) -> VideoFrame:
        """获取指定帧信息"""
        frame = db.query(VideoFrame).filter(VideoFrame.id == frame_id).first()
        if not frame:
            raise HTTPException(status_code=404, detail="帧不存在")
        return frame
    
    def get_frame_image_path(self, frame_id: int, db: Session) -> str:
        """获取帧图片文件路径"""
        frame = self.get_frame(frame_id, db)
        
        # 检查图片文件是否存在
        if not os.path.exists(frame.frame_path):
            raise HTTPException(status_code=404, detail="帧图片文件不存在")
        
        return frame.frame_path
    
    def delete_video_frames(self, video_id: int, db: Session) -> dict:
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
        frames_dir = Path(f"{self.frames_storage_path}/video_{video_id}")
        if frames_dir.exists() and not any(frames_dir.iterdir()):
            frames_dir.rmdir()
        
        return {
            "message": "视频帧删除完成",
            "video_id": video_id,
            "deleted_frames": len(frames),
            "deleted_files": deleted_files
        }
    
    def get_frame_statistics(self, video_id: int, db: Session) -> dict:
        """获取视频帧统计信息"""
        frames = db.query(VideoFrame).filter(VideoFrame.video_id == video_id).all()
        
        if not frames:
            return {
                "total_frames": 0,
                "total_size": 0,
                "duration_ms": 0,
                "avg_frame_size": 0
            }
        
        total_size = sum(frame.file_size or 0 for frame in frames)
        duration_ms = max(frame.timestamp_ms for frame in frames) if frames else 0
        avg_frame_size = total_size / len(frames) if frames else 0
        
        return {
            "total_frames": len(frames),
            "total_size": total_size,
            "duration_ms": duration_ms,
            "avg_frame_size": avg_frame_size
        }
    
    def delete_frame(self, frame_id: int, db: Session) -> dict:
        """删除指定帧"""
        frame = db.query(VideoFrame).filter(VideoFrame.id == frame_id).first()
        if not frame:
            raise HTTPException(status_code=404, detail="帧不存在")
        
        # 删除文件
        if os.path.exists(frame.frame_path):
            try:
                os.remove(frame.frame_path)
            except Exception as e:
                print(f"删除帧文件失败: {frame.frame_path}, 错误: {e}")
        
        # 删除数据库记录
        db.delete(frame)
        db.commit()
        
        return {
            "message": "帧删除成功",
            "frame_id": frame_id
        }


# 创建全局帧提取器实例
frame_extractor = FrameExtractor()