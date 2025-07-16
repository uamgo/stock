"""
东方财富数据获取器

基于原有的data.est模块，提供统一的数据获取接口
"""

import sys
from pathlib import Path
from typing import Optional
import pandas as pd

# 添加原有模块路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "data"))

from ...core.data_fetcher import DataFetcher
from ...config.logging_config import get_logger

class EastmoneyDataFetcher(DataFetcher):
    """东方财富数据获取器"""
    
    def __init__(self, cache_enabled: bool = True):
        """
        初始化数据获取器
        
        Args:
            cache_enabled: 是否启用缓存
        """
        super().__init__(cache_enabled)
        self.logger = get_logger("eastmoney_fetcher")
        
        # 导入原有模块
        try:
            from data.est.req import est_daily, est_prepare_data
            self.daily_fetcher = est_daily.EastmoneyDailyStockFetcher()
            self.prepare_data = est_prepare_data
        except ImportError as e:
            self.logger.error(f"Failed to import legacy modules: {e}")
            self.daily_fetcher = None
            self.prepare_data = None
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表
        
        Returns:
            股票列表数据
        """
        cache_key = "stock_list"
        
        # 尝试从缓存获取
        cached_data = self.get_from_cache(cache_key, expire_minutes=60)
        if cached_data is not None:
            self.logger.info("Loaded stock list from cache")
            return cached_data
        
        try:
            if self.prepare_data is None:
                raise ImportError("prepare_data module not available")
            
            # 从原有模块获取数据
            members_df = self.prepare_data.load_members_df_from_path()
            
            if members_df is None or members_df.empty:
                self.logger.warning("No stock list data available")
                return pd.DataFrame()
            
            # 保存到缓存
            self.save_to_cache(cache_key, members_df)
            
            self.logger.info(f"Loaded {len(members_df)} stocks from data source")
            return members_df
            
        except Exception as e:
            self.logger.error(f"Failed to get stock list: {e}")
            return pd.DataFrame()
    
    def get_daily_data(self, stock_code: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        获取日线数据
        
        Args:
            stock_code: 股票代码
            days: 天数
            
        Returns:
            日线数据
        """
        cache_key = f"daily_{stock_code}_{days}"
        
        # 尝试从缓存获取
        cached_data = self.get_from_cache(cache_key, expire_minutes=10)
        if cached_data is not None:
            return cached_data
        
        try:
            if self.daily_fetcher is None:
                raise ImportError("daily_fetcher not available")
            
            # 从原有模块获取数据
            daily_df = self.daily_fetcher.get_daily_df(stock_code)
            
            if daily_df is None or daily_df.empty:
                return None
            
            # 取最近指定天数的数据
            if len(daily_df) > days:
                daily_df = daily_df.tail(days)
            
            # 保存到缓存
            self.save_to_cache(cache_key, daily_df)
            
            return daily_df
            
        except Exception as e:
            self.logger.error(f"Failed to get daily data for {stock_code}: {e}")
            return None
    
    def get_minute_data(self, stock_code: str, minutes: int = 240) -> Optional[pd.DataFrame]:
        """
        获取分钟数据
        
        Args:
            stock_code: 股票代码
            minutes: 分钟数
            
        Returns:
            分钟数据
        """
        # 目前原有系统不支持分钟数据，返回空
        self.logger.warning("Minute data not supported by legacy system")
        return None
    
    def get_concept_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取概念板块数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            概念数据
        """
        cache_key = f"concept_{stock_code}"
        
        # 尝试从缓存获取
        cached_data = self.get_from_cache(cache_key, expire_minutes=60)
        if cached_data is not None:
            return cached_data
        
        try:
            # 这里可以添加概念数据获取逻辑
            # 目前返回空DataFrame
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Failed to get concept data for {stock_code}: {e}")
            return None
