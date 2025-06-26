# -*- coding: utf-8 -*-
"""
OCR识别模块
负责视频帧的OCR识别、关键词分析等功能
"""

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from models_simple import Video, VideoFrame, OCRResult, StageConfig, ProcessStatus
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from paddleocr import PaddleOCR
import json
import os


class OCRProcessRequest(BaseModel):
    use_gpu: Optional[bool] = False
    lang: Optional[str] = "ch"  # 语言：ch, en等


class OCRResultResponse(BaseModel):
    id: int
    frame_id: int
    text_content: Optional[str]
    confidence: Optional[float]
    bbox: Optional[dict]
    processed_at: datetime
    
    class Config:
        from_attributes = True


class KeywordAnalysisRequest(BaseModel):
    keywords: List[str]
    analysis_type: Optional[str] = "appearance"  # appearance, disappearance, both


class KeywordAnalysisResponse(BaseModel):
    keyword: str
    first_appearance_timestamp: Optional[int]
    first_disappearance_timestamp: Optional[int]
    total_occurrences: int
    frame_occurrences: List[dict]


class OCRProcessor:
    """OCR处理器"""
    
    def __init__(self):
        self.ocr_instance = None
        self.ocr_results_path = "./data/ocr_results"
        
        # 确保OCR结果存储目录存在
        Path(self.ocr_results_path).mkdir(parents=True, exist_ok=True)
        
        # 初始化OCR实例
        self.initialize_ocr()
    
    def initialize_ocr(self, use_gpu: bool = False, lang: str = "ch") -> None:
        """初始化OCR实例"""
        try:
            self.ocr_instance = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                lang=lang,
                use_gpu=use_gpu
            )
            print(f"✓ PaddleOCR初始化完成 (GPU: {use_gpu}, 语言: {lang})")
        except Exception as e:
            print(f"⚠ PaddleOCR初始化失败: {e}")
            self.ocr_instance = None
    
    def process_frame_ocr(self, frame_path: str, frame_id: int, use_gpu: bool = False, lang: str = "ch") -> dict:
        """对单个帧进行OCR识别"""
        if not self.ocr_instance:
            raise ValueError("OCR实例未初始化")
        
        if not os.path.exists(frame_path):
            raise ValueError(f"帧图片文件不存在: {frame_path}")
        
        try:
            # 执行OCR识别
            result = self.ocr_instance.ocr(frame_path, cls=True)
            
            # 处理OCR结果
            ocr_data = {
                "frame_id": frame_id,
                "text_blocks": [],
                "full_text": "",
                "total_confidence": 0.0
            }
            
            if result and result[0]:
                text_blocks = []
                confidences = []
                full_text_parts = []
                
                for line in result[0]:
                    if len(line) >= 2:
                        bbox = line[0]  # 边界框坐标
                        text_info = line[1]  # 文本和置信度
                        
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                            text = text_info[0]
                            confidence = float(text_info[1])
                            
                            text_block = {
                                "text": text,
                                "confidence": confidence,
                                "bbox": bbox
                            }
                            
                            text_blocks.append(text_block)
                            confidences.append(confidence)
                            full_text_parts.append(text)
                
                ocr_data["text_blocks"] = text_blocks
                ocr_data["full_text"] = " ".join(full_text_parts)
                ocr_data["total_confidence"] = sum(confidences) / len(confidences) if confidences else 0.0
            
            return ocr_data
            
        except Exception as e:
            raise ValueError(f"OCR处理失败: {str(e)}")
    
    def save_ocr_result_to_file(self, video_id: int, frame_number: int, ocr_data: dict) -> str:
        """保存OCR结果到JSON文件"""
        ocr_output_dir = Path(f"{self.ocr_results_path}/video_{video_id}")
        ocr_output_dir.mkdir(parents=True, exist_ok=True)
        
        ocr_json_path = ocr_output_dir / f"frame_{frame_number}_ocr.json"
        with open(ocr_json_path, 'w', encoding='utf-8') as f:
            json.dump(ocr_data, f, ensure_ascii=False, indent=2)
        
        return str(ocr_json_path)
    
    async def process_video_ocr(self, video_id: int, request: OCRProcessRequest, db: Session) -> dict:
        """对视频的所有帧进行OCR处理"""
        # 检查视频是否存在
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 获取视频的所有帧
        frames = db.query(VideoFrame).filter(VideoFrame.video_id == video_id).order_by(VideoFrame.frame_number).all()
        if not frames:
            raise HTTPException(status_code=404, detail="视频帧不存在，请先进行分帧处理")
        
        try:
            # 更新视频状态为处理中
            video.process_status = ProcessStatus.processing
            db.commit()
            
            processed_frames = 0
            failed_frames = 0
            ocr_results = []
            
            for frame in frames:
                try:
                    # 检查是否已经处理过OCR
                    existing_ocr = db.query(OCRResult).filter(OCRResult.frame_id == frame.id).first()
                    if existing_ocr:
                        continue
                    
                    # 处理OCR
                    ocr_data = self.process_frame_ocr(frame.frame_path, frame.id, request.use_gpu, request.lang)
                    
                    # 保存OCR结果到数据库
                    db_ocr = OCRResult(
                        frame_id=frame.id,
                        text_content=ocr_data["full_text"],
                        confidence=ocr_data["total_confidence"],
                        bbox=json.dumps(ocr_data["text_blocks"], ensure_ascii=False)
                    )
                    
                    db.add(db_ocr)
                    processed_frames += 1
                    
                    # 保存OCR结果到JSON文件
                    self.save_ocr_result_to_file(video_id, frame.frame_number, ocr_data)
                    
                    ocr_results.append({
                        "frame_id": frame.id,
                        "frame_number": frame.frame_number,
                        "timestamp_ms": frame.timestamp_ms,
                        "text_content": ocr_data["full_text"],
                        "confidence": ocr_data["total_confidence"],
                        "text_blocks_count": len(ocr_data["text_blocks"])
                    })
                    
                except Exception as e:
                    failed_frames += 1
                    print(f"处理帧 {frame.id} OCR失败: {e}")
            
            # 批量提交数据库更改
            db.commit()
            
            # 更新视频状态为完成
            video.process_status = ProcessStatus.completed
            db.commit()
            
            return {
                "message": "OCR处理完成",
                "video_id": video_id,
                "total_frames": len(frames),
                "processed_frames": processed_frames,
                "failed_frames": failed_frames,
                "ocr_results": ocr_results[:10]  # 只返回前10个结果作为示例
            }
            
        except Exception as e:
            # 更新视频状态为失败
            video.process_status = ProcessStatus.failed
            db.commit()
            raise HTTPException(status_code=500, detail=f"OCR处理失败: {str(e)}")
    
    def get_video_ocr_results(self, video_id: int, db: Session) -> List[OCRResult]:
        """获取视频的所有OCR结果"""
        # 检查视频是否存在
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 获取OCR结果
        ocr_results = db.query(OCRResult).join(
            VideoFrame, OCRResult.frame_id == VideoFrame.id
        ).filter(
            VideoFrame.video_id == video_id
        ).order_by(VideoFrame.timestamp_ms).all()
        
        return ocr_results
    
    def get_frame_ocr_result(self, frame_id: int, db: Session) -> OCRResult:
        """获取指定帧的OCR结果"""
        ocr_result = db.query(OCRResult).filter(OCRResult.frame_id == frame_id).first()
        if not ocr_result:
            raise HTTPException(status_code=404, detail="帧OCR结果不存在")
        return ocr_result
    
    def analyze_keywords_in_ocr_results(self, video_id: int, keywords: List[str], db: Session) -> List[dict]:
        """分析OCR结果中的关键词出现和消失模式"""
        # 获取视频的所有帧和OCR结果
        frames_with_ocr = db.query(VideoFrame, OCRResult).join(
            OCRResult, VideoFrame.id == OCRResult.frame_id
        ).filter(
            VideoFrame.video_id == video_id
        ).order_by(VideoFrame.timestamp_ms).all()
        
        if not frames_with_ocr:
            return []
        
        # 分析每个关键词
        analysis_results = []
        
        for keyword in keywords:
            keyword_analysis = {
                "keyword": keyword,
                "first_appearance_timestamp": None,
                "first_disappearance_timestamp": None,
                "total_occurrences": 0,
                "frame_occurrences": [],
                "pattern_analysis": {
                    "continuous_periods": [],
                    "gap_periods": []
                }
            }
            
            previous_found = False
            current_period_start = None
            
            for frame, ocr_result in frames_with_ocr:
                # 检查关键词是否在OCR文本中
                text_content = ocr_result.text_content or ""
                found_in_frame = keyword.lower() in text_content.lower()
                
                if found_in_frame:
                    keyword_analysis["total_occurrences"] += 1
                    keyword_analysis["frame_occurrences"].append({
                        "frame_id": frame.id,
                        "timestamp_ms": frame.timestamp_ms,
                        "confidence": float(ocr_result.confidence) if ocr_result.confidence else 0.0
                    })
                    
                    # 记录第一次出现
                    if keyword_analysis["first_appearance_timestamp"] is None:
                        keyword_analysis["first_appearance_timestamp"] = frame.timestamp_ms
                    
                    # 开始连续期间
                    if not previous_found:
                        current_period_start = frame.timestamp_ms
                
                else:
                    # 关键词消失
                    if previous_found:
                        # 记录第一次消失
                        if keyword_analysis["first_disappearance_timestamp"] is None:
                            keyword_analysis["first_disappearance_timestamp"] = frame.timestamp_ms
                        
                        # 结束连续期间
                        if current_period_start is not None:
                            keyword_analysis["pattern_analysis"]["continuous_periods"].append({
                                "start_timestamp": current_period_start,
                                "end_timestamp": frame.timestamp_ms,
                                "duration_ms": frame.timestamp_ms - current_period_start
                            })
                            current_period_start = None
                
                previous_found = found_in_frame
            
            # 处理最后一个连续期间
            if current_period_start is not None and frames_with_ocr:
                last_frame = frames_with_ocr[-1][0]
                keyword_analysis["pattern_analysis"]["continuous_periods"].append({
                    "start_timestamp": current_period_start,
                    "end_timestamp": last_frame.timestamp_ms,
                    "duration_ms": last_frame.timestamp_ms - current_period_start
                })
            
            analysis_results.append(keyword_analysis)
        
        return analysis_results
    
    async def analyze_video_keywords(self, video_id: int, request: KeywordAnalysisRequest, db: Session) -> dict:
        """分析视频中关键词的出现和消失模式"""
        # 检查视频是否存在
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 检查是否有OCR结果
        ocr_count = db.query(OCRResult).join(
            VideoFrame, OCRResult.frame_id == VideoFrame.id
        ).filter(
            VideoFrame.video_id == video_id
        ).count()
        
        if ocr_count == 0:
            raise HTTPException(status_code=404, detail="视频OCR结果不存在，请先进行OCR处理")
        
        try:
            # 执行关键词分析
            analysis_results = self.analyze_keywords_in_ocr_results(video_id, request.keywords, db)
            
            return {
                "message": "关键词分析完成",
                "video_id": video_id,
                "analyzed_keywords": len(request.keywords),
                "analysis_results": analysis_results
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"关键词分析失败: {str(e)}")
    
    async def analyze_stage_keywords(self, video_id: int, db: Session) -> dict:
        """基于stage_configs分析关键词模式"""
        # 检查视频是否存在
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 获取视频的阶段配置
        stage_configs = db.query(StageConfig).filter(
            StageConfig.video_id == video_id
        ).order_by(StageConfig.stage_order).all()
        
        if not stage_configs:
            raise HTTPException(status_code=404, detail="视频阶段配置不存在")
        
        # 检查是否有OCR结果
        ocr_count = db.query(OCRResult).join(
            VideoFrame, OCRResult.frame_id == VideoFrame.id
        ).filter(
            VideoFrame.video_id == video_id
        ).count()
        
        if ocr_count == 0:
            raise HTTPException(status_code=404, detail="视频OCR结果不存在，请先进行OCR处理")
        
        try:
            stage_analysis_results = []
            
            for config in stage_configs:
                # 解析关键词
                keywords = json.loads(config.keywords) if isinstance(config.keywords, str) else config.keywords
                
                # 分析关键词
                analysis_results = self.analyze_keywords_in_ocr_results(video_id, keywords, db)
                
                stage_analysis_results.append({
                    "stage_id": config.id,
                    "stage_name": config.stage_name,
                    "stage_order": config.stage_order,
                    "keywords": keywords,
                    "keyword_analysis": analysis_results
                })
            
            return {
                "message": "阶段关键词分析完成",
                "video_id": video_id,
                "total_stages": len(stage_configs),
                "stage_analysis_results": stage_analysis_results
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"阶段关键词分析失败: {str(e)}")
    
    async def analyze_keywords_by_stage_config(self, config_id: int, db: Session) -> dict:
        """基于阶段配置进行关键词分析"""
        try:
            # 获取阶段配置
            stage_config = db.query(StageConfig).filter(StageConfig.id == config_id).first()
            if not stage_config:
                raise HTTPException(status_code=404, detail="阶段配置不存在")
            
            # 解析关键词
            keywords = json.loads(stage_config.keywords) if isinstance(stage_config.keywords, str) else stage_config.keywords
            if not keywords:
                raise HTTPException(status_code=400, detail="阶段配置中没有关键词")
            
            # 执行关键词分析
            analysis_results = self.analyze_keywords_in_ocr_results(stage_config.video_id, keywords, db)
            
            return {
                "message": "基于阶段配置的关键词分析完成",
                "stage_config_id": config_id,
                "video_id": stage_config.video_id,
                "stage_name": stage_config.stage_name,
                "keywords_count": len(keywords),
                "analysis_results": analysis_results
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"关键词分析失败: {str(e)}")


# 创建全局OCR处理器实例
ocr_processor = OCRProcessor()