"""
策略基类

定义所有交易策略的基础接口和通用方法
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, time

from ..config.trading_config import TradingConfig
from ..config.logging_config import get_logger

class BaseStrategy(ABC):
    """交易策略基类"""
    
    def __init__(self, config: TradingConfig = None):
        """
        初始化策略
        
        Args:
            config: 交易配置
        """
        self.config = config or TradingConfig()
        self.logger = get_logger(f"strategy.{self.__class__.__name__}")
        self.name = self.__class__.__name__
    
    @abstractmethod
    def select_stocks(self, stocks_data: pd.DataFrame) -> pd.DataFrame:
        """
        选择股票
        
        Args:
            stocks_data: 股票数据
            
        Returns:
            选中的股票数据
        """
        pass
    
    @abstractmethod
    def calculate_score(self, stock_data: Dict[str, Any]) -> float:
        """
        计算股票评分
        
        Args:
            stock_data: 股票数据
            
        Returns:
            评分 (0-100)
        """
        pass
    
    def calculate_risk_score(self, stock_data: Dict[str, Any]) -> float:
        """
        计算风险评分
        
        Args:
            stock_data: 股票数据
            
        Returns:
            风险评分 (0-100, 越低越安全)
        """
        risk_score = 0
        
        # 位置风险
        position_ratio = stock_data.get('position_ratio', 0)
        if position_ratio > 0.8:
            risk_score += 30
        elif position_ratio > 0.6:
            risk_score += 15
        
        # 量比风险
        volume_ratio = stock_data.get('volume_ratio', 0)
        if volume_ratio > 2.5:
            risk_score += 25
        elif volume_ratio > 2.0:
            risk_score += 10
        
        # 涨跌幅风险
        pct_chg = stock_data.get('pct_chg', 0)
        if pct_chg > 5:
            risk_score += 20
        elif pct_chg > 4:
            risk_score += 10
        
        # 技术形态风险
        upper_shadow = stock_data.get('upper_shadow', 0)
        body_length = stock_data.get('body_length', 1)
        if upper_shadow > body_length * 0.3:
            risk_score += 15
        
        return min(risk_score, 100)
    
    def is_trading_time(self) -> tuple[bool, str]:
        """
        判断当前是否为交易时间
        
        Returns:
            (是否为交易时间, 时间状态描述)
        """
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()
        
        # 周末
        if weekday in [5, 6]:
            return False, "周末休市"
        
        # 交易日时间判断
        morning_start = time(9, 30)
        morning_end = time(11, 30)
        afternoon_start = time(13, 0)
        afternoon_end = time(15, 0)
        
        if current_time < morning_start:
            return False, "开盘前"
        elif current_time > afternoon_end:
            return False, "收盘后"
        elif morning_end <= current_time <= afternoon_start:
            return False, "午休时间"
        else:
            return True, "交易时间"
    
    def get_timing_advice(self) -> List[str]:
        """
        获取时机建议
        
        Returns:
            时机建议列表
        """
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()
        
        advice = []
        
        # 周内时机判断
        if weekday == 4:  # 周五
            advice.append("⚠️  今日为周五，建议谨慎操作（周末风险）")
        elif weekday in [5, 6]:  # 周末
            advice.append("❌ 当前为周末，市场休市")
        elif weekday in [0, 1, 2]:  # 周一到周三
            advice.append("✅ 今日为周一至周三，操作时机良好")
        elif weekday == 3:  # 周四
            advice.append("🟡 今日为周四，操作可行但需关注周五风险")
        
        # 日内时机判断
        tail_start = time(14, 30)
        tail_end = time(15, 0)
        golden_end = time(14, 50)
        
        if tail_start <= current_time <= tail_end:
            if current_time <= golden_end:
                advice.append("🟢 当前为黄金买入时段（14:30-14:50）")
            else:
                advice.append("🟡 当前为最后确认时段（14:50-15:00）")
        elif current_time < tail_start and current_time > time(9, 30):
            advice.append("⏰ 建议等待14:30后再考虑买入")
        elif current_time > tail_end:
            advice.append("⏰ 今日交易已结束，可为明日做准备")
        else:
            advice.append("⏰ 市场未开盘")
        
        return advice
    
    def validate_stock_data(self, stock_data: Dict[str, Any]) -> bool:
        """
        验证股票数据完整性
        
        Args:
            stock_data: 股票数据
            
        Returns:
            是否有效
        """
        required_fields = ['code', 'name', 'close', 'pct_chg', 'volume_ratio']
        
        for field in required_fields:
            if field not in stock_data or stock_data[field] is None:
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        return True
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略信息
        
        Returns:
            策略信息字典
        """
        return {
            "name": self.name,
            "version": "1.0.0",
            "description": "Base strategy class",
            "config": self.config.to_dict(),
            "created_at": datetime.now().isoformat()
        }
