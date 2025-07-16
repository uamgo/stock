"""
全局配置管理

包含系统级配置和常量定义
"""

import os
from pathlib import Path
from typing import Dict, Any

class Settings:
    """全局配置类"""
    
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    
    # 数据目录
    DATA_DIR = PROJECT_ROOT / "data"
    CACHE_DIR = DATA_DIR / "cache"
    EXPORTS_DIR = DATA_DIR / "exports"
    BACKUPS_DIR = DATA_DIR / "backups"
    
    # 日志目录
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # 配置文件路径
    CONFIG_FILE = PROJECT_ROOT / "config.json"
    USER_CONFIG_FILE = Path.home() / ".tail_trading_config.json"
    
    # 数据库配置
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "stock_trading")
    
    # 交易相关配置
    TRADING_HOURS = {
        "morning_start": "09:30",
        "morning_end": "11:30",
        "afternoon_start": "13:00",
        "afternoon_end": "15:00",
        "tail_trading_start": "14:30",
        "tail_trading_end": "15:00",
        "golden_time_start": "14:30",
        "golden_time_end": "14:50"
    }
    
    # 工作日配置
    WORKING_DAYS = [0, 1, 2, 3, 4]  # 周一到周五
    
    # 默认输出路径
    DEFAULT_OUTPUT_DIR = Path.home() / "Downloads"
    
    # API配置
    API_TIMEOUT = 30
    API_RETRY_COUNT = 3
    API_RETRY_DELAY = 1
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 缓存配置
    CACHE_ENABLED = True
    CACHE_EXPIRE_MINUTES = 10
    
    @classmethod
    def ensure_directories(cls):
        """确保所有必需的目录存在"""
        for dir_path in [cls.DATA_DIR, cls.CACHE_DIR, cls.EXPORTS_DIR, 
                        cls.BACKUPS_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "project_root": str(cls.PROJECT_ROOT),
            "data_dir": str(cls.DATA_DIR),
            "logs_dir": str(cls.LOGS_DIR),
            "trading_hours": cls.TRADING_HOURS,
            "working_days": cls.WORKING_DAYS,
            "mongodb_uri": cls.MONGODB_URI,
            "database_name": cls.DATABASE_NAME,
            "api_timeout": cls.API_TIMEOUT,
            "log_level": cls.LOG_LEVEL,
            "cache_enabled": cls.CACHE_ENABLED
        }
