"""
A股尾盘交易系统

专业的A股尾盘交易系统，基于技术分析实现智能选股和交易管理。

主要模块:
- config: 配置管理
- core: 核心业务逻辑
- strategies: 交易策略
- data: 数据处理
- utils: 工具函数
- cli: 命令行接口
"""

__version__ = "3.0.0"
__author__ = "Stock Trading Team"
__email__ = "team@stocktrading.com"

# 导入核心类
try:
    from .core.strategy import BaseStrategy
    from .core.data_fetcher import DataFetcher
    from .core.risk_manager import RiskManager
    from .core.position_manager import PositionManager
    
    # 导入主要策略
    from .strategies.tail_up_strategy import TailUpStrategy
    
    # 导入配置
    from .config.settings import Settings
    from .config.trading_config import TradingConfig
    
    __all__ = [
        "BaseStrategy",
        "DataFetcher", 
        "RiskManager",
        "PositionManager",
        "TailUpStrategy",
        "Settings",
        "TradingConfig"
    ]
    
except ImportError as e:
    # 如果导入失败，提供基本信息
    print(f"Warning: Some modules could not be imported: {e}")
    __all__ = []
