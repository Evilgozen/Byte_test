from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.engine import Engine
from pathlib import Path
import os
from typing import Generator, Optional
import logging

try:
    from config import get_settings, get_storage_path
except ImportError:
    # 如果config模块不存在，使用默认配置
    def get_settings():
        class DefaultSettings:
            database_url = "sqlite:///./video_analysis.db"
            database_echo = True
            storage_base_path = "./data"
        return DefaultSettings()
    
    def get_storage_path():
        return Path("./data")

from models import *

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self, database_url: str = "sqlite:///./video_analysis.db"):
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=True,  # 开发环境下显示SQL语句
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
    
    def create_tables(self):
        """创建所有数据库表"""
        try:
            SQLModel.metadata.create_all(self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return Session(self.engine)


class StorageManager:
    """存储管理类"""
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.video_path = self.base_path / "videos"
        self.frame_path = self.base_path / "frames"
        self.chart_path = self.base_path / "charts"
        self.temp_path = self.base_path / "temp"
        self.backup_path = self.base_path / "backups"
    
    def create_directories(self):
        """创建所有必要的目录结构"""
        directories = [
            self.base_path,
            self.video_path,
            self.frame_path,
            self.chart_path,
            self.temp_path,
            self.backup_path,
            self.temp_path / "uploads",
            self.temp_path / "processing",
            self.backup_path / "db_backups",
            self.backup_path / "file_backups"
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"目录创建成功: {directory}")
            except Exception as e:
                logger.error(f"目录创建失败 {directory}: {e}")
                raise
    
    def create_video_directory(self, project_id: int, year: int, month: int) -> Path:
        """为特定项目和时间创建视频目录"""
        video_dir = self.video_path / str(year) / f"{month:02d}" / f"project_{project_id}"
        video_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"视频目录创建成功: {video_dir}")
        return video_dir
    
    def create_frame_directory(self, video_id: int) -> Path:
        """为特定视频创建帧目录"""
        frame_dir = self.frame_path / f"video_{video_id}"
        frame_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"帧目录创建成功: {frame_dir}")
        return frame_dir
    
    def create_chart_directory(self, year: int, month: int) -> Path:
        """创建图表目录"""
        chart_dir = self.chart_path / str(year) / f"{month:02d}"
        chart_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"图表目录创建成功: {chart_dir}")
        return chart_dir
    
    def get_video_path(self, project_id: int, year: int, month: int, filename: str) -> Path:
        """获取视频文件完整路径"""
        return self.create_video_directory(project_id, year, month) / filename
    
    def get_frame_path(self, video_id: int, frame_filename: str) -> Path:
        """获取帧文件完整路径"""
        return self.create_frame_directory(video_id) / frame_filename
    
    def get_chart_path(self, year: int, month: int, chart_filename: str) -> Path:
        """获取图表文件完整路径"""
        return self.create_chart_directory(year, month) / chart_filename
    
    def cleanup_temp_files(self, hours: int = 24):
        """清理临时文件"""
        import time
        cutoff_time = time.time() - (hours * 3600)
        
        for temp_dir in [self.temp_path / "uploads", self.temp_path / "processing"]:
            if temp_dir.exists():
                for file_path in temp_dir.iterdir():
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            logger.info(f"清理临时文件: {file_path}")
                        except Exception as e:
                            logger.error(f"清理临时文件失败 {file_path}: {e}")


class DatabaseService:
    """数据库服务类"""
    
    def __init__(self, database_url: str = "sqlite:///./video_analysis.db", storage_path: str = "./data"):
        self.db_config = DatabaseConfig(database_url)
        self.storage_manager = StorageManager(storage_path)
    
    def initialize(self):
        """初始化数据库和存储目录"""
        logger.info("开始初始化数据库和存储系统...")
        
        # 创建存储目录
        self.storage_manager.create_directories()
        
        # 创建数据库表
        self.db_config.create_tables()
        
        logger.info("数据库和存储系统初始化完成")
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.db_config.get_session()
    
    def get_storage_manager(self) -> StorageManager:
        """获取存储管理器"""
        return self.storage_manager


# 全局数据库服务实例
db_service = DatabaseService()


def get_database_service() -> DatabaseService:
    """获取数据库服务实例"""
    return db_service


def get_db_session() -> Session:
    """获取数据库会话的依赖注入函数"""
    with db_service.get_session() as session:
        yield session


if __name__ == "__main__":
    # 直接运行此文件时初始化数据库
    db_service.initialize()
    print("数据库初始化完成！")