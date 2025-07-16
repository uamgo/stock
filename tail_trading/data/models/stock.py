"""
数据模型定义

定义系统中使用的数据结构
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class StockStatus(Enum):
    """股票状态枚举"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELISTED = "delisted"

class TradeAction(Enum):
    """交易动作枚举"""
    BUY = "buy"
    SELL = "sell"

class PositionStatus(Enum):
    """持仓状态枚举"""
    HOLDING = "holding"
    SOLD = "sold"
    STOPPED = "stopped"

@dataclass
class Stock:
    """股票信息"""
    code: str
    name: str
    market: str  # SH, SZ
    industry: str = ""
    concept: str = ""
    status: StockStatus = StockStatus.ACTIVE
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Stock":
        """从字典创建"""
        return cls(**data)

@dataclass
class DailyData:
    """日线数据"""
    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    pct_chg: float
    turnover: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DailyData":
        """从字典创建"""
        return cls(**data)

@dataclass
class TechnicalIndicators:
    """技术指标"""
    code: str
    date: str
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    volume_ratio: float = 0.0
    rsi: float = 0.0
    macd: float = 0.0
    kdj_k: float = 0.0
    kdj_d: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TechnicalIndicators":
        """从字典创建"""
        return cls(**data)

@dataclass
class SelectionResult:
    """选股结果"""
    code: str
    name: str
    score: float
    risk_score: float
    probability: float
    reasons: List[str]
    indicators: Dict[str, Any]
    selected_time: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SelectionResult":
        """从字典创建"""
        return cls(**data)
