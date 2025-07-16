"""
数据获取器

统一的数据获取接口，支持多种数据源
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from ..config.logging_config import get_logger
from ..config.settings import Settings

class DataFetcher(ABC):
    """数据获取器基类"""
    
    def __init__(self, cache_enabled: bool = True):
        """
        初始化数据获取器
        
        Args:
            cache_enabled: 是否启用缓存
        """
        self.cache_enabled = cache_enabled
        self.logger = get_logger(f"data.{self.__class__.__name__}")
        self.cache_dir = Settings.CACHE_DIR
        Settings.ensure_directories()
    
    @abstractmethod
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表
        
        Returns:
            股票列表数据
        """
        pass
    
    @abstractmethod
    def get_daily_data(self, stock_code: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        获取日线数据
        
        Args:
            stock_code: 股票代码
            days: 天数
            
        Returns:
            日线数据
        """
        pass
    
    @abstractmethod
    def get_minute_data(self, stock_code: str, minutes: int = 240) -> Optional[pd.DataFrame]:
        """
        获取分钟数据
        
        Args:
            stock_code: 股票代码
            minutes: 分钟数
            
        Returns:
            分钟数据
        """
        pass
    
    def get_cache_path(self, cache_key: str) -> Path:
        """
        获取缓存文件路径
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存文件路径
        """
        return self.cache_dir / f"{cache_key}.pkl"
    
    def get_from_cache(self, cache_key: str, expire_minutes: int = 10) -> Optional[pd.DataFrame]:
        """
        从缓存获取数据
        
        Args:
            cache_key: 缓存键
            expire_minutes: 过期时间（分钟）
            
        Returns:
            缓存数据或None
        """
        if not self.cache_enabled:
            return None
        
        cache_path = self.get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        # 检查缓存是否过期
        cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - cache_time > timedelta(minutes=expire_minutes):
            return None
        
        try:
            return pd.read_pickle(cache_path)
        except Exception as e:
            self.logger.warning(f"Failed to load cache {cache_key}: {e}")
            return None
    
    def save_to_cache(self, cache_key: str, data: pd.DataFrame) -> None:
        """
        保存数据到缓存
        
        Args:
            cache_key: 缓存键
            data: 数据
        """
        if not self.cache_enabled:
            return
        
        cache_path = self.get_cache_path(cache_key)
        
        try:
            data.to_pickle(cache_path)
        except Exception as e:
            self.logger.warning(f"Failed to save cache {cache_key}: {e}")
    
    def clear_cache(self) -> None:
        """清理缓存"""
        if not self.cache_dir.exists():
            return
        
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to remove cache file {cache_file}: {e}")
    
    def get_batch_data(self, stock_codes: List[str], data_type: str = "daily") -> Dict[str, pd.DataFrame]:
        """
        批量获取数据
        
        Args:
            stock_codes: 股票代码列表
            data_type: 数据类型 ("daily" 或 "minute")
            
        Returns:
            股票代码到数据的映射
        """
        results = {}
        
        for code in stock_codes:
            try:
                if data_type == "daily":
                    data = self.get_daily_data(code)
                elif data_type == "minute":
                    data = self.get_minute_data(code)
                else:
                    raise ValueError(f"Unknown data type: {data_type}")
                
                if data is not None and not data.empty:
                    results[code] = data
                    
            except Exception as e:
                self.logger.error(f"Failed to get {data_type} data for {code}: {e}")
                continue
        
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        return {
            "fetcher_name": self.__class__.__name__,
            "cache_enabled": self.cache_enabled,
            "cache_dir": str(self.cache_dir),
            "cache_files_count": len(list(self.cache_dir.glob("*.pkl"))) if self.cache_dir.exists() else 0,
            "last_check": datetime.now().isoformat()
        }
