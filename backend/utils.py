import os
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
import uuid


def generate_video_filename(project_id: int, original_name: str) -> str:
    """生成视频文件名
    
    Args:
        project_id: 项目ID
        original_name: 原始文件名
    
    Returns:
        生成的文件名
    """
    timestamp = int(time.time())
    ext = os.path.splitext(original_name)[1]
    return f"video_{project_id}_{timestamp}{ext}"


def generate_frame_filename(frame_number: int, ext: str = ".jpg") -> str:
    """生成帧文件名
    
    Args:
        frame_number: 帧序号
        ext: 文件扩展名
    
    Returns:
        生成的帧文件名
    """
    return f"frame_{frame_number:06d}{ext}"


def generate_chart_filename(video_id: int, chart_type: str, ext: str = ".png") -> str:
    """生成图表文件名
    
    Args:
        video_id: 视频ID
        chart_type: 图表类型
        ext: 文件扩展名
    
    Returns:
        生成的图表文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"video_{video_id}_{chart_type}_{timestamp}{ext}"


def generate_unique_filename(original_name: str, prefix: str = "") -> str:
    """生成唯一文件名
    
    Args:
        original_name: 原始文件名
        prefix: 文件名前缀
    
    Returns:
        唯一的文件名
    """
    name, ext = os.path.splitext(original_name)
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    
    if prefix:
        return f"{prefix}_{name}_{timestamp}_{unique_id}{ext}"
    else:
        return f"{name}_{timestamp}_{unique_id}{ext}"


def calculate_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256)
    
    Returns:
        文件哈希值
    """
    hash_func = getattr(hashlib, algorithm)()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def get_file_size(file_path: str) -> int:
    """获取文件大小
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件大小（字节）
    """
    return os.path.getsize(file_path)


def ensure_directory_exists(directory_path: str) -> Path:
    """确保目录存在
    
    Args:
        directory_path: 目录路径
    
    Returns:
        Path对象
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_video_info_from_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """从文件名获取视频信息
    
    Args:
        filename: 文件名
    
    Returns:
        (格式, 扩展名)
    """
    ext = os.path.splitext(filename)[1].lower()
    format_map = {
        '.mp4': 'mp4',
        '.avi': 'avi',
        '.mov': 'mov',
        '.mkv': 'mkv',
        '.wmv': 'wmv',
        '.flv': 'flv',
        '.webm': 'webm'
    }
    
    video_format = format_map.get(ext)
    return video_format, ext


def format_duration(duration_ms: int) -> str:
    """格式化时长显示
    
    Args:
        duration_ms: 时长（毫秒）
    
    Returns:
        格式化的时长字符串
    """
    if duration_ms < 1000:
        return f"{duration_ms}ms"
    
    seconds = duration_ms // 1000
    ms = duration_ms % 1000
    
    if seconds < 60:
        return f"{seconds}.{ms:03d}s"
    
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m{seconds:02d}.{ms:03d}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    return f"{hours}h{minutes:02d}m{seconds:02d}.{ms:03d}s"


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        格式化的文件大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes}B"
    
    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.1f}KB"
    
    size_mb = size_kb / 1024
    if size_mb < 1024:
        return f"{size_mb:.1f}MB"
    
    size_gb = size_mb / 1024
    return f"{size_gb:.1f}GB"


def validate_video_file(file_path: str) -> bool:
    """验证是否为有效的视频文件
    
    Args:
        file_path: 文件路径
    
    Returns:
        是否为有效视频文件
    """
    if not os.path.exists(file_path):
        return False
    
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    ext = os.path.splitext(file_path)[1].lower()
    
    return ext in video_extensions


def clean_filename(filename: str) -> str:
    """清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
    
    Returns:
        清理后的文件名
    """
    import re
    
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(illegal_chars, '_', filename)
    
    # 移除多余的空格和点
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'\.+', '.', cleaned)
    
    # 确保文件名不为空
    if not cleaned or cleaned == '.':
        cleaned = f"file_{int(time.time())}"
    
    return cleaned


def get_timestamp_from_frame_number(frame_number: int, fps: float) -> int:
    """根据帧号和帧率计算时间戳
    
    Args:
        frame_number: 帧号
        fps: 帧率
    
    Returns:
        时间戳（毫秒）
    """
    if fps <= 0:
        return 0
    
    return int((frame_number / fps) * 1000)


def get_frame_number_from_timestamp(timestamp_ms: int, fps: float) -> int:
    """根据时间戳和帧率计算帧号
    
    Args:
        timestamp_ms: 时间戳（毫秒）
        fps: 帧率
    
    Returns:
        帧号
    """
    if fps <= 0:
        return 0
    
    return int((timestamp_ms / 1000) * fps)