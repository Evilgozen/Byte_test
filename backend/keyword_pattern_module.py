# -*- coding: utf-8 -*-
"""
关键词模式匹配模块
用于分析视频中关键词的出现和消失模式，返回第一次出现和第一次消失的时间戳
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from models_simple import Video, VideoFrame, OCRResult, StageConfig
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import json
from datetime import datetime


class KeywordPatternRequest(BaseModel):
    """关键词模式分析请求模型"""
    keywords: List[str]
    case_sensitive: bool = False
    exact_match: bool = False
    confidence_threshold: float = 0.0


class KeywordOccurrence(BaseModel):
    """关键词出现记录"""
    frame_id: int
    frame_number: int
    timestamp_ms: int
    confidence: float
    text_content: str
    matched_text: str


class KeywordPatternResult(BaseModel):
    """关键词模式分析结果"""
    keyword: str
    first_appearance_timestamp_ms: Optional[int] = None
    first_disappearance_timestamp_ms: Optional[int] = None
    last_appearance_timestamp_ms: Optional[int] = None
    total_occurrences: int = 0
    continuous_duration_ms: Optional[int] = None
    gap_duration_ms: Optional[int] = None
    occurrences: List[KeywordOccurrence] = []
    pattern_analysis: Dict[str, Any] = {}


class StagePatternRequest(BaseModel):
    """阶段模式分析请求模型"""
    stage_id: Optional[int] = None
    confidence_threshold: float = 0.0
    include_pattern_details: bool = True


class StagePatternResult(BaseModel):
    """阶段模式分析结果"""
    stage_id: int
    stage_name: str
    stage_order: int
    keywords: List[str]
    stage_start_timestamp_ms: Optional[int] = None
    stage_end_timestamp_ms: Optional[int] = None
    stage_duration_ms: Optional[int] = None
    keyword_results: List[KeywordPatternResult] = []
    pattern_summary: Dict[str, Any] = {}


class KeywordPatternAnalyzer:
    """关键词模式分析器"""
    
    def __init__(self):
        pass
    
    def analyze_keyword_pattern(self, video_id: int, request: KeywordPatternRequest, db: Session) -> Dict[str, Any]:
        """分析视频中关键词的模式"""
        # 验证视频存在
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 获取视频的所有帧和OCR结果
        frames_with_ocr = db.query(VideoFrame, OCRResult).join(
            OCRResult, VideoFrame.id == OCRResult.frame_id
        ).filter(
            VideoFrame.video_id == video_id,
            OCRResult.confidence >= request.confidence_threshold
        ).order_by(VideoFrame.timestamp_ms).all()
        
        if not frames_with_ocr:
            raise HTTPException(status_code=404, detail="视频OCR结果不存在或不满足置信度要求")
        
        # 分析每个关键词
        keyword_results = []
        for keyword in request.keywords:
            result = self._analyze_single_keyword(
                keyword, frames_with_ocr, request.case_sensitive, request.exact_match
            )
            keyword_results.append(result)
        
        return {
            "message": "关键词模式分析完成",
            "video_id": video_id,
            "analyzed_keywords": len(request.keywords),
            "total_frames": len(frames_with_ocr),
            "analysis_timestamp": datetime.now().isoformat(),
            "keyword_results": [result.dict() for result in keyword_results],
            "summary": self._generate_analysis_summary(keyword_results)
        }
    
    def analyze_stage_pattern(self, video_id: int, request: StagePatternRequest, db: Session) -> Dict[str, Any]:
        """基于阶段配置分析关键词模式"""
        # 验证视频存在
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 获取阶段配置
        if request.stage_id:
            stage_configs = db.query(StageConfig).filter(
                StageConfig.id == request.stage_id,
                StageConfig.video_id == video_id
            ).all()
        else:
            stage_configs = db.query(StageConfig).filter(
                StageConfig.video_id == video_id
            ).order_by(StageConfig.stage_order).all()
        
        if not stage_configs:
            raise HTTPException(status_code=404, detail="阶段配置不存在")
        
        # 获取视频的所有帧和OCR结果
        frames_with_ocr = db.query(VideoFrame, OCRResult).join(
            OCRResult, VideoFrame.id == OCRResult.frame_id
        ).filter(
            VideoFrame.video_id == video_id,
            OCRResult.confidence >= request.confidence_threshold
        ).order_by(VideoFrame.timestamp_ms).all()
        
        if not frames_with_ocr:
            raise HTTPException(status_code=404, detail="视频OCR结果不存在或不满足置信度要求")
        
        # 分析每个阶段
        stage_results = []
        for config in stage_configs:
            # 解析关键词
            keywords = json.loads(config.keywords) if isinstance(config.keywords, str) else config.keywords
            
            # 分析阶段关键词
            keyword_results = []
            for keyword in keywords:
                result = self._analyze_single_keyword(keyword, frames_with_ocr, False, False)
                keyword_results.append(result)
            
            # 计算阶段时间范围
            stage_start = None
            stage_end = None
            
            if keyword_results:
                # 找到最早的关键词出现时间作为阶段开始
                first_appearances = [r.first_appearance_timestamp_ms for r in keyword_results if r.first_appearance_timestamp_ms is not None]
                if first_appearances:
                    stage_start = min(first_appearances)
                
                # 找到最晚的关键词消失时间作为阶段结束
                last_disappearances = [r.first_disappearance_timestamp_ms for r in keyword_results if r.first_disappearance_timestamp_ms is not None]
                if last_disappearances:
                    stage_end = max(last_disappearances)
            
            stage_duration = None
            if stage_start is not None and stage_end is not None:
                stage_duration = stage_end - stage_start
            
            stage_result = StagePatternResult(
                stage_id=config.id,
                stage_name=config.stage_name,
                stage_order=config.stage_order,
                keywords=keywords,
                stage_start_timestamp_ms=stage_start,
                stage_end_timestamp_ms=stage_end,
                stage_duration_ms=stage_duration,
                keyword_results=keyword_results,
                pattern_summary=self._generate_stage_summary(keyword_results)
            )
            
            stage_results.append(stage_result)
        
        return {
            "message": "阶段模式分析完成",
            "video_id": video_id,
            "total_stages": len(stage_configs),
            "analysis_timestamp": datetime.now().isoformat(),
            "stage_results": [result.dict() for result in stage_results],
            "overall_summary": self._generate_overall_summary(stage_results)
        }
    
    def _analyze_single_keyword(self, keyword: str, frames_with_ocr: List, case_sensitive: bool = False, exact_match: bool = False) -> KeywordPatternResult:
        """分析单个关键词的模式"""
        result = KeywordPatternResult(keyword=keyword)
        
        previous_found = False
        continuous_start = None
        continuous_periods = []
        gap_periods = []
        last_found_timestamp = None
        
        for frame, ocr_result in frames_with_ocr:
            text_content = ocr_result.text_content or ""
            
            # 关键词匹配逻辑
            if exact_match:
                # 精确匹配
                if case_sensitive:
                    found_in_frame = keyword == text_content.strip()
                else:
                    found_in_frame = keyword.lower() == text_content.strip().lower()
            else:
                # 包含匹配
                if case_sensitive:
                    found_in_frame = keyword in text_content
                else:
                    found_in_frame = keyword.lower() in text_content.lower()
            
            if found_in_frame:
                # 记录出现
                occurrence = KeywordOccurrence(
                    frame_id=frame.id,
                    frame_number=frame.frame_number,
                    timestamp_ms=frame.timestamp_ms,
                    confidence=float(ocr_result.confidence) if ocr_result.confidence else 0.0,
                    text_content=text_content,
                    matched_text=keyword
                )
                result.occurrences.append(occurrence)
                result.total_occurrences += 1
                
                # 记录第一次出现
                if result.first_appearance_timestamp_ms is None:
                    result.first_appearance_timestamp_ms = frame.timestamp_ms
                
                # 更新最后出现时间
                result.last_appearance_timestamp_ms = frame.timestamp_ms
                
                # 开始连续期间
                if not previous_found:
                    continuous_start = frame.timestamp_ms
                
                last_found_timestamp = frame.timestamp_ms
            
            else:
                # 关键词消失
                if previous_found:
                    # 记录第一次消失
                    if result.first_disappearance_timestamp_ms is None:
                        result.first_disappearance_timestamp_ms = frame.timestamp_ms
                    
                    # 结束连续期间
                    if continuous_start is not None:
                        continuous_periods.append({
                            "start_timestamp_ms": continuous_start,
                            "end_timestamp_ms": frame.timestamp_ms,
                            "duration_ms": frame.timestamp_ms - continuous_start
                        })
                        continuous_start = None
                    
                    # 记录间隔期间
                    if last_found_timestamp is not None:
                        gap_periods.append({
                            "start_timestamp_ms": last_found_timestamp,
                            "end_timestamp_ms": frame.timestamp_ms,
                            "duration_ms": frame.timestamp_ms - last_found_timestamp
                        })
            
            previous_found = found_in_frame
        
        # 处理最后一个连续期间
        if continuous_start is not None and frames_with_ocr:
            last_frame = frames_with_ocr[-1][0]
            continuous_periods.append({
                "start_timestamp_ms": continuous_start,
                "end_timestamp_ms": last_frame.timestamp_ms,
                "duration_ms": last_frame.timestamp_ms - continuous_start
            })
        
        # 计算连续持续时间
        if continuous_periods:
            result.continuous_duration_ms = sum(period["duration_ms"] for period in continuous_periods)
        
        # 计算间隔持续时间
        if gap_periods:
            result.gap_duration_ms = sum(period["duration_ms"] for period in gap_periods)
        
        # 生成模式分析
        result.pattern_analysis = {
            "continuous_periods": continuous_periods,
            "gap_periods": gap_periods,
            "average_confidence": sum(occ.confidence for occ in result.occurrences) / len(result.occurrences) if result.occurrences else 0.0,
            "occurrence_frequency": len(result.occurrences),
            "time_span_ms": (result.last_appearance_timestamp_ms - result.first_appearance_timestamp_ms) if result.first_appearance_timestamp_ms and result.last_appearance_timestamp_ms else 0
        }
        
        return result
    
    def _generate_analysis_summary(self, keyword_results: List[KeywordPatternResult]) -> Dict[str, Any]:
        """生成分析摘要"""
        total_keywords = len(keyword_results)
        found_keywords = len([r for r in keyword_results if r.total_occurrences > 0])
        total_occurrences = sum(r.total_occurrences for r in keyword_results)
        
        earliest_appearance = None
        latest_disappearance = None
        
        for result in keyword_results:
            if result.first_appearance_timestamp_ms is not None:
                if earliest_appearance is None or result.first_appearance_timestamp_ms < earliest_appearance:
                    earliest_appearance = result.first_appearance_timestamp_ms
            
            if result.first_disappearance_timestamp_ms is not None:
                if latest_disappearance is None or result.first_disappearance_timestamp_ms > latest_disappearance:
                    latest_disappearance = result.first_disappearance_timestamp_ms
        
        return {
            "total_keywords_analyzed": total_keywords,
            "keywords_found": found_keywords,
            "keywords_not_found": total_keywords - found_keywords,
            "total_occurrences": total_occurrences,
            "earliest_appearance_timestamp_ms": earliest_appearance,
            "latest_disappearance_timestamp_ms": latest_disappearance,
            "analysis_time_span_ms": (latest_disappearance - earliest_appearance) if earliest_appearance and latest_disappearance else 0
        }
    
    def _generate_stage_summary(self, keyword_results: List[KeywordPatternResult]) -> Dict[str, Any]:
        """生成阶段摘要"""
        return {
            "keywords_found": len([r for r in keyword_results if r.total_occurrences > 0]),
            "total_occurrences": sum(r.total_occurrences for r in keyword_results),
            "average_confidence": sum(r.pattern_analysis.get("average_confidence", 0) for r in keyword_results) / len(keyword_results) if keyword_results else 0.0
        }
    
    def _generate_overall_summary(self, stage_results: List[StagePatternResult]) -> Dict[str, Any]:
        """生成整体摘要"""
        total_stages = len(stage_results)
        active_stages = len([s for s in stage_results if s.stage_start_timestamp_ms is not None])
        
        earliest_stage_start = None
        latest_stage_end = None
        
        for stage in stage_results:
            if stage.stage_start_timestamp_ms is not None:
                if earliest_stage_start is None or stage.stage_start_timestamp_ms < earliest_stage_start:
                    earliest_stage_start = stage.stage_start_timestamp_ms
            
            if stage.stage_end_timestamp_ms is not None:
                if latest_stage_end is None or stage.stage_end_timestamp_ms > latest_stage_end:
                    latest_stage_end = stage.stage_end_timestamp_ms
        
        return {
            "total_stages": total_stages,
            "active_stages": active_stages,
            "inactive_stages": total_stages - active_stages,
            "earliest_stage_start_timestamp_ms": earliest_stage_start,
            "latest_stage_end_timestamp_ms": latest_stage_end,
            "total_analysis_duration_ms": (latest_stage_end - earliest_stage_start) if earliest_stage_start and latest_stage_end else 0
        }


# 创建全局实例
keyword_pattern_analyzer = KeywordPatternAnalyzer()