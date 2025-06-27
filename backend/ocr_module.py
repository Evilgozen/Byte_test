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
    raw_result: Optional[List[Dict[str, Any]]] = None
    
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
        self.ocr_images_path = "./data/ocr_images"  # 新增OCR图片存储路径
        
        # 确保OCR结果存储目录存在
        Path(self.ocr_results_path).mkdir(parents=True, exist_ok=True)
        Path(self.ocr_images_path).mkdir(parents=True, exist_ok=True)  # 创建OCR图片目录
        
        # 初始化OCR实例
        self.initialize_ocr()
    
    def initialize_ocr(self, use_gpu: bool = False, lang: str = "ch") -> None:
        """初始化OCR实例 - 使用用户推荐的PaddleOCR配置"""
        try:
            # 使用用户推荐的PaddleOCR配置参数
            self.ocr_instance = PaddleOCR(
                use_doc_orientation_classify=False,  # 不使用文档方向分类模型
                use_doc_unwarping=False,  # 不使用文本图像矫正模型
                use_textline_orientation=False,  # 不使用文本行方向分类模型
                lang=lang,  # 语言设置
                use_gpu=use_gpu,  # GPU设置
                show_log=False  # 减少日志输出
            )
            print("✓ PaddleOCR配置初始化成功（使用推荐配置）")
            
        except Exception as e:
            print(f"⚠ OCR初始化失败: {e}")
            # 最基本的配置作为备选
            try:
                self.ocr_instance = PaddleOCR(
                    use_angle_cls=True, 
                    lang=lang
                )
                print("✓ 使用基础PaddleOCR配置")
            except Exception as fallback_e:
                print(f"⚠ 基础配置也失败: {fallback_e}")
                raise ValueError(f"OCR初始化完全失败: {fallback_e}")
    
    def process_frame_ocr(self, frame_path: str, frame_id: int, video_id: int = None, use_gpu: bool = False, lang: str = 'ch', save_raw_result: bool = True) -> dict:
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
            
            # 执行OCR识别 - 使用新版predict API
            print(f"🔍 开始OCR识别: {frame_path}")
            
            # 尝试使用新版predict API
            try:
                result = self.ocr_instance.predict(frame_path)
                print(f"📝 OCR原始结果（新版API）: {result}")
                
                # 保存OCR处理后的图片
                if video_id is not None:
                    ocr_image_dir = Path(f"{self.ocr_images_path}/video_{video_id}")
                    ocr_image_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 保存OCR结果图片（使用指定格式）
                    for res in result:
                        # 直接保存为指定格式的文件名
                        ocr_image_name = f"frame_{frame_id:06d}_333ms_ocr_res_img.jpg"
                        ocr_image_path = ocr_image_dir / ocr_image_name
                        res.save_to_img(save_path=str(ocr_image_path))
                        print(f"✅ OCR图片已保存: {ocr_image_path}")
                    
                    # 保存原始OCR结果到JSON文件（如果需要）
                    if save_raw_result:
                        raw_result_dir = Path(f"{self.ocr_results_path}/video_{video_id}")
                        raw_result_dir.mkdir(parents=True, exist_ok=True)
                        raw_json_name = f"frame_{frame_id:06d}_333ms_ocr_res.json"
                        raw_result_path = raw_result_dir / raw_json_name
                        
                        # 将原始结果转换为可序列化的格式
                        raw_data = {
                            "frame_id": frame_id,
                            "frame_path": frame_path,
                            "ocr_version": "PP-OCRv5",
                            "processing_time": round(time.time() - start_time, 3),
                            "raw_result": self._serialize_ocr_result(result)
                        }
                        
                        with open(raw_result_path, 'w', encoding='utf-8') as f:
                            json.dump(raw_data, f, ensure_ascii=False, indent=2, default=str)
                        print(f"✅ 原始OCR结果已保存: {raw_result_path}")
                else:
                    print("⚠ 未提供video_id，跳过OCR图片保存")
                
                # 转换新版API结果为旧版格式以保持兼容性
                result = self._convert_new_api_result_to_old_format(result)
                
            except Exception as new_api_error:
                print(f"⚠ 新版API失败，尝试旧版API: {new_api_error}")
                # 回退到旧版API
                result = self.ocr_instance.ocr(frame_path)
                print(f"📝 OCR原始结果（旧版API）: {result}")
            
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
    
    def _convert_new_api_result_to_old_format(self, output):
        """转换新版predict API结果为旧版ocr格式"""
        try:
            converted_result = []
            
            for res in output:
                # 新版API返回的结果对象，需要提取文本和置信度信息
                if hasattr(res, 'rec_texts') and hasattr(res, 'rec_scores'):
                    # 如果有rec_texts和rec_scores属性
                    for text, score in zip(res.rec_texts, res.rec_scores):
                        if text.strip():  # 只处理非空文本
                            # 模拟边界框坐标
                            bbox = [[0, 0], [100, 0], [100, 30], [0, 30]]
                            converted_result.append([bbox, [text, float(score)]])
                elif hasattr(res, 'text') and hasattr(res, 'confidence'):
                    # 如果有text和confidence属性
                    bbox = [[0, 0], [100, 0], [100, 30], [0, 30]]
                    converted_result.append([bbox, [res.text, float(res.confidence)]])
                else:
                    # 尝试其他可能的属性结构
                    print(f"⚠ 未知的结果格式: {type(res)}, 属性: {dir(res)}")
            
            return [converted_result] if converted_result else [[]]
            
        except Exception as e:
            print(f"新版API结果转换失败: {e}")
            return [[]]
    
    def _convert_new_api_result(self, output, frame_path: str):
        """转换新版API结果为旧版格式（保留原方法以兼容）"""
        return self._convert_new_api_result_to_old_format(output)
    
    def _serialize_ocr_result(self, result):
        """将OCR结果序列化为可保存的格式"""
        try:
            serialized_result = []
            
            for res in result:
                if hasattr(res, '__dict__'):
                    # 如果是对象，尝试提取所有属性
                    res_dict = {}
                    for attr_name in dir(res):
                        if not attr_name.startswith('_'):  # 跳过私有属性
                            try:
                                attr_value = getattr(res, attr_name)
                                if not callable(attr_value):  # 跳过方法
                                    # 处理numpy数组
                                    if hasattr(attr_value, 'tolist'):
                                        res_dict[attr_name] = attr_value.tolist()
                                    else:
                                        res_dict[attr_name] = attr_value
                            except Exception:
                                continue
                    serialized_result.append(res_dict)
                else:
                    # 如果是基本类型或列表，直接处理
                    if hasattr(res, 'tolist'):
                        serialized_result.append(res.tolist())
                    else:
                        serialized_result.append(res)
            
            return serialized_result
            
        except Exception as e:
            print(f"序列化OCR结果失败: {e}")
            return str(result)  # 回退到字符串表示
    
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
                    ocr_data = self.process_frame_ocr(frame.frame_path, frame.id, video_id, request.use_gpu, request.lang, save_raw_result=True)
                    print(f"✅ 帧 {frame.id} OCR处理完成，文本数量: {ocr_data.get('text_count', 0)}")
                    
                    # 从JSON文件中提取rec_texts数组
                    rec_texts = []
                    try:
                        # 读取保存的JSON文件获取rec_texts
                        json_file_path = f"data/ocr_results/video_{video_id}/frame_{frame.id:06d}_333ms_ocr_res.json"
                        if os.path.exists(json_file_path):
                            with open(json_file_path, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                                if 'raw_result' in json_data and json_data['raw_result']:
                                    for raw_item in json_data['raw_result']:
                                        if isinstance(raw_item, dict) and 'json' in raw_item:
                                            json_res = raw_item['json']
                                            if isinstance(json_res, dict) and 'res' in json_res:
                                                res_data = json_res['res']
                                                if isinstance(res_data, dict) and 'rec_texts' in res_data:
                                                    rec_texts = res_data['rec_texts']
                                                    break
                    except Exception as e:
                        print(f"读取rec_texts失败: {e}")
                        rec_texts = []
                    
                    # 如果没有找到rec_texts，使用备用方案
                    if not rec_texts:
                        rec_texts = [block.get('text', '') for block in ocr_data.get('text_blocks', [])]
                    
                    # 保存OCR结果到数据库
                    db_ocr = OCRResult(
                        frame_id=frame.id,
                        text_content=json.dumps(rec_texts, ensure_ascii=False),  # 存储rec_texts数组
                        confidence=ocr_data["total_confidence"],
                        bbox=json.dumps(ocr_data["text_blocks"], ensure_ascii=False)
                    )
                    
                    db.add(db_ocr)
                    processed_frames += 1
                    
                    # 注释掉普通格式JSON的保存，只保留raw格式
                    # self.save_ocr_result_to_file(video_id, frame.frame_number, ocr_data)
                    
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
            video_ocr_dir = os.path.join("data", "ocr_results", f"video_{video_id}")
            
            # 检查目录是否存在
            if not os.path.exists(video_ocr_dir):
                print(f"OCR结果目录不存在: {video_ocr_dir}")
                return []
            
            # 查找该视频的所有OCR结果文件
            for filename in os.listdir(video_ocr_dir):
                if filename.endswith("_ocr_res.json"):
                    file_path = os.path.join(video_ocr_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            ocr_data = json.load(f)
                            
                            # 手动构建EnhancedOCRResultResponse对象
                            enhanced_result = EnhancedOCRResultResponse(
                                frame_id=ocr_data.get('frame_id', 0),
                                frame_path=ocr_data.get('frame_path', ''),
                                ocr_version=ocr_data.get('ocr_version', 'PP-OCRv5'),
                                processing_time=ocr_data.get('processing_time', 0.0),
                                text_blocks=[],  # 简化处理
                                full_text='',  # 从raw_result中提取
                                total_confidence=0.0,  # 从raw_result中计算
                                text_count=0,  # 从raw_result中计算
                                language='zh',  # 默认中文
                                image_info={},  # 简化处理
                                detection_results=[],  # 简化处理
                                recognition_results=[],  # 简化处理
                                raw_result=ocr_data.get('raw_result', [])
                            )
                            
                            # 从raw_result中提取rec_texts
                            raw_result = ocr_data.get('raw_result', [])
                            all_texts = []
                            for result in raw_result:
                                if isinstance(result, dict) and 'json' in result:
                                    json_data = result['json']
                                    if isinstance(json_data, dict) and 'res' in json_data:
                                        res_data = json_data['res']
                                        if isinstance(res_data, dict) and 'rec_texts' in res_data:
                                            all_texts.extend(res_data['rec_texts'])
                            
                            enhanced_result.full_text = ' '.join(all_texts)
                            enhanced_result.text_count = len(all_texts)
                            
                            enhanced_results.append(enhanced_result)
                            
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
            json_files_count = 0
            if ocr_output_dir.exists():
                json_files_count = len(list(ocr_output_dir.glob("*.json")))
            
            # 检查OCR图片存储
            ocr_image_dir = Path(f"{self.ocr_images_path}/video_{video_id}")
            image_files_count = 0
            if ocr_image_dir.exists():
                image_files_count = len(list(ocr_image_dir.glob("*.jpg")))
            
            return {
                "video_id": video_id,
                "total_frames": total_frames,
                "database_ocr_records": db_ocr_count,
                "json_files_count": json_files_count,
                "ocr_images_count": image_files_count,
                "storage_paths": {
                    "ocr_results": str(ocr_output_dir),
                    "ocr_images": str(ocr_image_dir)
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取OCR存储信息失败: {str(e)}")
    
    def get_video_ocr_images(self, video_id: int) -> List[dict]:
        """获取视频的所有OCR处理后图片列表"""
        try:
            ocr_image_dir = Path(f"{self.ocr_images_path}/video_{video_id}")
            if not ocr_image_dir.exists():
                return []
            
            ocr_images = []
            for image_file in ocr_image_dir.glob("*.jpg"):
                # 从文件名提取frame_id
                filename = image_file.stem  # 去掉扩展名
                if filename.startswith("frame_") and filename.endswith("_ocr"):
                    try:
                        frame_id = int(filename.split("_")[1])
                        file_stat = image_file.stat()
                        
                        ocr_images.append({
                            "frame_id": frame_id,
                            "filename": image_file.name,
                            "file_path": str(image_file),
                            "file_size": file_stat.st_size,
                            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                        })
                    except (ValueError, IndexError) as e:
                        print(f"解析OCR图片文件名失败: {filename}, 错误: {e}")
                        continue
            
            # 按frame_id排序
            ocr_images.sort(key=lambda x: x["frame_id"])
            return ocr_images
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取OCR图片列表失败: {str(e)}")
    
    def get_frame_ocr_image_path(self, video_id: int, frame_id: int) -> str:
        """获取指定帧的OCR图片路径"""
        ocr_image_path = Path(f"{self.ocr_images_path}/video_{video_id}/frame_{frame_id}_ocr.jpg")
        if not ocr_image_path.exists():
            raise HTTPException(status_code=404, detail="OCR图片不存在")
        return str(ocr_image_path)
    
    def delete_video_ocr_images(self, video_id: int) -> dict:
        """删除视频的所有OCR图片"""
        try:
            ocr_image_dir = Path(f"{self.ocr_images_path}/video_{video_id}")
            deleted_files = 0
            
            if ocr_image_dir.exists():
                for image_file in ocr_image_dir.glob("*.jpg"):
                    try:
                        image_file.unlink()
                        deleted_files += 1
                    except Exception as e:
                        print(f"删除OCR图片失败: {image_file}, 错误: {e}")
                
                # 如果目录为空，删除目录
                try:
                    if not any(ocr_image_dir.iterdir()):
                        ocr_image_dir.rmdir()
                except Exception as e:
                    print(f"删除OCR图片目录失败: {ocr_image_dir}, 错误: {e}")
            
            return {
                "message": "OCR图片删除成功",
                "video_id": video_id,
                "deleted_files": deleted_files
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除OCR图片失败: {str(e)}")
    
    def view_video_ocr_results(self, video_id: int, db: Session) -> dict:
        """查看视频的OCR结果（包含数据库和JSON文件信息）"""
        try:
            # 获取数据库中的OCR结果
            db_results = self.get_video_ocr_results(video_id, db)
            
            # 获取JSON文件中的增强OCR结果
            json_results = self.get_enhanced_ocr_results(video_id)
            
            # 统计信息
            stats = {
                "video_id": video_id,
                "database_records_count": len(db_results),
                "json_files_count": len(json_results),
                "data_consistency": len(db_results) == len(json_results)
            }
            
            # 返回完整信息
            return {
                "stats": stats,
                "database_results": [{
                    "id": result.id,
                    "frame_id": result.frame_id,
                    "text_content": self._parse_text_content(result.text_content),
                    "confidence": float(result.confidence) if result.confidence else None,
                    "bbox": result.bbox,
                    "processed_at": result.processed_at.isoformat() if result.processed_at else None
                } for result in db_results],
                "json_results": [{
                    "frame_id": result.frame_id,
                    "frame_path": result.frame_path,
                    "ocr_version": result.ocr_version,
                    "processing_time": result.processing_time,
                    "text_blocks_count": len(result.text_blocks) if result.text_blocks else 0,
                    "has_raw_result": result.raw_result is not None
                } for result in json_results]
            }
            
        except Exception as e:
            print(f"查看OCR结果失败: {e}")
            raise HTTPException(status_code=500, detail=f"查看OCR结果失败: {str(e)}")
    
    def _parse_text_content(self, text_content: str):
        """解析数据库中存储的text_content字段"""
        try:
            # 尝试解析为JSON数组（新格式）
            parsed = json.loads(text_content)
            if isinstance(parsed, list):
                return parsed  # 返回rec_texts数组
            else:
                return text_content  # 返回原始字符串
        except (json.JSONDecodeError, TypeError):
            # 如果解析失败，返回原始字符串
            return text_content
    
    def delete_frame_ocr_image(self, video_id: int, frame_id: int) -> dict:
        """删除指定帧的OCR图片"""
        try:
            ocr_image_path = Path(f"{self.ocr_images_path}/video_{video_id}/frame_{frame_id}_ocr.jpg")
            
            if not ocr_image_path.exists():
                raise HTTPException(status_code=404, detail="OCR图片不存在")
            
            ocr_image_path.unlink()
            
            return {
                "message": "OCR图片删除成功",
                "video_id": video_id,
                "frame_id": frame_id,
                "deleted_file": str(ocr_image_path)
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除OCR图片失败: {str(e)}")


# 创建全局OCR处理器实例
ocr_processor = OCRProcessor()