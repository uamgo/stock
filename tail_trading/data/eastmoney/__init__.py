"""
东方财富数据模块

提供东方财富数据源的统一接口
"""

from .daily_fetcher import EastmoneyDataFetcher

__all__ = [
    "EastmoneyDataFetcher"
]
