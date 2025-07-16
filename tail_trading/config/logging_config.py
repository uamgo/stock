"""
日志配置管理

统一的日志配置和管理
"""

import logging
import logging.handlers
from pathlib import Path
from .settings import Settings

def setup_logging(log_level: str = None) -> logging.Logger:
    """
    设置日志配置
    
    Args:
        log_level: 日志级别
        
    Returns:
        配置好的日志器
    """
    if log_level is None:
        log_level = Settings.LOG_LEVEL
    
    # 确保日志目录存在
    Settings.ensure_directories()
    
    # 创建日志器
    logger = logging.getLogger("tail_trading")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 如果已经有处理器，不重复添加
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(Settings.LOG_FORMAT)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    log_file = Settings.LOGS_DIR / "trading.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 错误日志处理器
    error_log_file = Settings.LOGS_DIR / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    if name is None:
        name = "tail_trading"
    
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logging()
    
    return logger
