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
from paddleocr import PaddleOCR, TextRecognition
from config import OCRConfig
import json
import os
import time
import cv2


class OCRProcessRequest(BaseModel):
    use_gpu: Optional[bool] = False
    lang: Optional[str] = "ch"  # 语言：ch, en等


class OCRResultResponse(BaseModel):
    id: int
    frame_id: int
    text_content: Optional[str]
    confidence: Optional[float]
    bbox: Optional[str]  # Store as JSON string to avoid serialization issues
    processed_at: datetime
    
    class Config:
        from_attributes = True


class EnhancedOCRResultResponse(BaseModel):
    """增强的OCR结果响应模型 - 支持PP-OCRv5"""
    frame_id: int
    frame_path: str
    ocr_version: str
    processing_time: float
    text_blocks: List[Dict[str, Any]]
    full_text: str
    total_confidence: float
    text_count: int
    language: str
    image_info: Dict[str, Any]
    detection_results: List[Dict[str, Any]]
    recognition_results: List[Dict[str, Any]]
    
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
        """初始化OCR实例 - 优化的PaddleOCR配置"""
        try:
            # 先尝试使用新版TextRecognition API
            try:
                self.text_recognition = TextRecognition()
                print("✓ TextRecognition模型初始化成功")
            except Exception as te:
                print(f"⚠ TextRecognition初始化失败: {te}")
                self.text_recognition = None
            
            # 使用优化的PaddleOCR配置
            self.ocr_instance = PaddleOCR(
                use_angle_cls=True, 
                lang='ch',
                show_log=False,  # 减少日志输出
                use_gpu=use_gpu
            )
            print("✓ PaddleOCR配置初始化成功")
            
        except Exception as e:
            print(f"⚠ OCR初始化失败: {e}")
            # 最基本的配置
            self.text_recognition = None
            self.ocr_instance = PaddleOCR(use_angle_cls=True, lang='ch')
            print("✓ 使用基础PaddleOCR配置")
    
    def process_frame_ocr(self, frame_path: str, frame_id: int, use_gpu: bool = False, lang: str = "ch") -> dict:
        """对单个帧进行OCR识别"""
        if not self.ocr_instance:
            raise ValueError("OCR实例未初始化")
        
        if not os.path.exists(frame_path):
            raise ValueError(f"帧图片文件不存在: {frame_path}")
        
        try:
            # 获取图像信息
            image = cv2.imread(frame_path)
            if image is None:
                print(f"⚠ 无法读取图像文件: {frame_path}")
                raise ValueError(f"无法读取图像文件: {frame_path}")
            
            image_height, image_width = image.shape[:2]
            image_channels = image.shape[2] if len(image.shape) > 2 else None
            print(f"📷 图像信息: {image_width}x{image_height}, 通道数: {image_channels}")
            
            # 记录处理开始时间
            start_time = time.time()
            
            # 执行OCR识别 - 使用旧版API（更稳定）
            print(f"🔍 开始OCR识别: {frame_path}")
            result = self.ocr_instance.ocr(frame_path)
            print(f"📝 OCR原始结果: {result}")
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 处理OCR结果 - 增强的JSON结构
            ocr_data = {
                "frame_id": frame_id,
                "frame_path": frame_path,
                "ocr_version": "PP-OCRv5",
                "processing_time": round(processing_time, 3),
                "text_blocks": [],
                "full_text": "",
                "total_confidence": 0.0,
                "text_count": 0,
                "language": lang,
                "image_info": {
                    "width": image_width,
                    "height": image_height,
                    "channels": image_channels
                },
                "detection_results": [],
                "recognition_results": []
            }
            
            # 处理不同格式的OCR结果
            if result:
                text_blocks = []
                confidences = []
                full_text_parts = []
                detection_results = []
                recognition_results = []
                
                # 检查是否是新版TextRecognition API的结果格式
                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                    # 新版API格式处理
                    result_dict = result[0]
                    if 'rec_texts' in result_dict and 'rec_scores' in result_dict:
                        rec_texts = result_dict['rec_texts']
                        rec_scores = result_dict['rec_scores']
                        
                        for idx, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                            if text.strip():  # 只处理非空文本
                                # 模拟边界框（新版API可能不提供详细坐标）
                                bbox = [[0, idx*20], [100, idx*20], [100, (idx+1)*20], [0, (idx+1)*20]]
                                
                                text_block = {
                                    "id": idx,
                                    "text": text,
                                    "confidence": float(score),
                                    "bbox": bbox,
                                    "bbox_normalized": {
                                        "x1": 0,
                                        "y1": idx*20,
                                        "x2": 100,
                                        "y2": (idx+1)*20
                                    },
                                    "text_length": len(text),
                                    "word_count": len(text.split()) if text.strip() else 0
                                }
                                
                                detection_result = {
                                    "id": idx,
                                    "bbox": bbox,
                                    "confidence": float(score)
                                }
                                
                                recognition_result = {
                                    "id": idx,
                                    "text": text,
                                    "confidence": float(score)
                                }
                                
                                text_blocks.append(text_block)
                                detection_results.append(detection_result)
                                recognition_results.append(recognition_result)
                                confidences.append(float(score))
                                full_text_parts.append(text)
                elif isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                     # 旧版API格式处理
                     for idx, line in enumerate(result[0]):
                         if len(line) >= 2:
                             bbox = line[0]  # 边界框坐标
                             text_info = line[1]  # 文本和置信度
                             
                             if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                 text = text_info[0]
                                 confidence = float(text_info[1])
                                 
                                 # 详细的文本块信息
                                 text_block = {
                                     "id": idx,
                                     "text": text,
                                     "confidence": confidence,
                                     "bbox": bbox,
                                     "bbox_normalized": {
                                         "x1": min([point[0] for point in bbox]),
                                         "y1": min([point[1] for point in bbox]),
                                         "x2": max([point[0] for point in bbox]),
                                         "y2": max([point[1] for point in bbox])
                                     },
                                     "text_length": len(text),
                                     "word_count": len(text.split()) if text.strip() else 0
                                 }
                                 
                                 # 检测结果
                                 detection_result = {
                                     "id": idx,
                                     "bbox": bbox,
                                     "confidence": confidence
                                 }
                                 
                                 # 识别结果
                                 recognition_result = {
                                     "id": idx,
                                     "text": text,
                                     "confidence": confidence,
                                     "char_confidences": []  # 可以扩展为字符级置信度
                                 }
                                 
                                 text_blocks.append(text_block)
                                 detection_results.append(detection_result)
                                 recognition_results.append(recognition_result)
                                 confidences.append(confidence)
                                 full_text_parts.append(text)
                
                ocr_data["text_blocks"] = text_blocks
                ocr_data["detection_results"] = detection_results
                ocr_data["recognition_results"] = recognition_results
                ocr_data["full_text"] = " ".join(full_text_parts)
                ocr_data["total_confidence"] = sum(confidences) / len(confidences) if confidences else 0.0
                ocr_data["text_count"] = len(text_blocks)
            
            return ocr_data
            
        except Exception as e:
            raise ValueError(f"OCR处理失败: {str(e)}")
    
    def _convert_new_api_result(self, output, frame_path: str):
        """转换新版API结果为旧版格式"""
        try:
            # 保存OCR处理后的图片和JSON
            output_dir = Path(f"{self.ocr_results_path}/ocr_output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存结果图片和JSON
            for res in output:
                res.save_to_img(save_path=str(output_dir))
                res.save_to_json(save_path=str(output_dir / "result.json"))
            
            # 转换为旧版格式 - 这里需要根据新版API的实际输出结构调整
            converted_result = []
            for res in output:
                # 新版API的结果结构可能不同，这里做基本转换
                # 具体转换逻辑需要根据实际API输出调整
                if hasattr(res, 'text') and hasattr(res, 'confidence'):
                    converted_result.append([
                        [[0, 0], [100, 0], [100, 30], [0, 30]],  # 默认边界框
                        [res.text, res.confidence]
                    ])
            
            return [converted_result] if converted_result else [[]]
            
        except Exception as e:
            print(f"新版API结果转换失败: {e}")
            return [[]]
    
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
                    print(f"🎬 处理帧: {frame.id}, 路径: {frame.frame_path}")
                    
                    # 检查是否已经处理过OCR
                    existing_ocr = db.query(OCRResult).filter(OCRResult.frame_id == frame.id).first()
                    if existing_ocr:
                        print(f"⏭ 跳过已处理的帧: {frame.id}")
                        continue
                    
                    # 处理OCR
                    print(f"🔍 开始处理帧 {frame.id} 的OCR")
                    ocr_data = self.process_frame_ocr(frame.frame_path, frame.id, request.use_gpu, request.lang)
                    print(f"✅ 帧 {frame.id} OCR处理完成，文本数量: {ocr_data.get('text_count', 0)}")
                    
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
    
    def get_enhanced_ocr_results(self, video_id: int) -> List[EnhancedOCRResultResponse]:
        """获取增强的OCR结果（从JSON文件读取）"""
        try:
            enhanced_results = []
            ocr_results_dir = os.path.join("data", "ocr_results")
            
            # 查找该视频的所有OCR结果文件
            for filename in os.listdir(ocr_results_dir):
                if filename.startswith(f"video_{video_id}_frame_") and filename.endswith(".json"):
                    file_path = os.path.join(ocr_results_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            ocr_data = json.load(f)
                            enhanced_results.append(EnhancedOCRResultResponse(**ocr_data))
                    except Exception as e:
                        print(f"读取OCR结果文件失败 {filename}: {e}")
                        continue
            
            # 按frame_id排序
            enhanced_results.sort(key=lambda x: x.frame_id)
            return enhanced_results
            
        except Exception as e:
            print(f"获取增强OCR结果失败: {e}")
            raise HTTPException(status_code=500, detail="获取增强OCR结果失败")
    
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
    
    def delete_video_ocr_results(self, video_id: int, db: Session) -> dict:
        """删除视频的所有OCR结果（数据库记录和JSON文件）"""
        try:
            # 检查视频是否存在
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise HTTPException(status_code=404, detail="视频不存在")
            
            # 获取视频的所有帧
            frames = db.query(VideoFrame).filter(VideoFrame.video_id == video_id).all()
            
            deleted_db_records = 0
            deleted_json_files = 0
            
            # 删除数据库中的OCR记录
            for frame in frames:
                ocr_results = db.query(OCRResult).filter(OCRResult.frame_id == frame.id).all()
                for ocr_result in ocr_results:
                    db.delete(ocr_result)
                    deleted_db_records += 1
            
            # 提交数据库更改
            db.commit()
            
            # 删除JSON文件
            ocr_output_dir = Path(f"{self.ocr_results_path}/video_{video_id}")
            if ocr_output_dir.exists():
                import shutil
                for json_file in ocr_output_dir.glob("*.json"):
                    try:
                        json_file.unlink()
                        deleted_json_files += 1
                    except Exception as e:
                        print(f"删除JSON文件失败: {json_file}, 错误: {e}")
                
                # 如果目录为空，删除目录
                try:
                    if not any(ocr_output_dir.iterdir()):
                        ocr_output_dir.rmdir()
                except Exception as e:
                    print(f"删除目录失败: {ocr_output_dir}, 错误: {e}")
            
            return {
                "message": "OCR结果删除成功",
                "video_id": video_id,
                "deleted_db_records": deleted_db_records,
                "deleted_json_files": deleted_json_files
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"删除OCR结果失败: {str(e)}")
    
    def get_ocr_storage_info(self, video_id: int, db: Session) -> dict:
        """获取OCR结果的存储信息"""
        try:
            # 检查视频是否存在
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise HTTPException(status_code=404, detail="视频不存在")
            
            # 统计数据库中的OCR记录
            frames = db.query(VideoFrame).filter(VideoFrame.video_id == video_id).all()
            total_frames = len(frames)
            
            db_ocr_count = 0
            for frame in frames:
                ocr_count = db.query(OCRResult).filter(OCRResult.frame_id == frame.id).count()
                db_ocr_count += ocr_count
            
            # 检查JSON文件存储
            ocr_output_dir = Path(f"{self.ocr_results_path}/video_{video_id}")
            json_files = []
            total_json_size = 0
            
            if ocr_output_dir.exists():
                for json_file in ocr_output_dir.glob("*.json"):
                    file_size = json_file.stat().st_size
                    json_files.append({
                        "filename": json_file.name,
                        "size_bytes": file_size,
                        "size_kb": round(file_size / 1024, 2)
                    })
                    total_json_size += file_size
            
            return {
                "video_id": video_id,
                "database_info": {
                    "total_frames": total_frames,
                    "ocr_records_count": db_ocr_count
                },
                "json_storage_info": {
                    "storage_path": str(ocr_output_dir),
                    "json_files_count": len(json_files),
                    "total_size_bytes": total_json_size,
                    "total_size_kb": round(total_json_size / 1024, 2),
                    "files": json_files[:10]  # 只显示前10个文件
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取OCR存储信息失败: {str(e)}")


# 创建全局OCR处理器实例
ocr_processor = OCRProcessor()