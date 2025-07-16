"""
交易配置管理

管理交易参数、策略配置和风险控制参数
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from .settings import Settings

@dataclass
class TradingConfig:
    """交易配置数据类"""
    
    # 基本策略参数
    min_pct_chg: float = 1.0          # 最小涨跌幅
    max_pct_chg: float = 6.0          # 最大涨跌幅
    min_volume_ratio: float = 1.1     # 最小量比
    max_volume_ratio: float = 3.0     # 最大量比
    max_position_ratio: float = 0.85  # 最大20日位置比例
    
    # 风险控制参数
    max_single_position: float = 0.10  # 单只股票最大仓位
    max_total_position: float = 0.70   # 总仓位上限
    stop_loss_ratio: float = -0.05     # 止损比例
    take_profit_ratio: float = 0.08    # 止盈比例
    max_consecutive_losses: int = 3     # 最大连续亏损次数
    
    # 技术指标参数
    ma_period: int = 20               # 均线周期
    volume_ma_period: int = 10        # 成交量均线周期
    min_shadow_ratio: float = 0.1     # 最小下影线比例
    max_upper_shadow_ratio: float = 0.5  # 最大上影线比例
    
    # 时间窗口参数
    lookback_days: int = 20           # 回看天数
    trend_days: int = 3               # 趋势判断天数
    
    # 评分权重
    price_weight: float = 0.25        # 价格权重
    volume_weight: float = 0.25       # 成交量权重
    technical_weight: float = 0.25    # 技术形态权重
    position_weight: float = 0.25     # 位置权重
    
    # 风险评分阈值
    low_risk_threshold: int = 40      # 低风险阈值
    medium_risk_threshold: int = 60   # 中风险阈值
    high_risk_threshold: int = 80     # 高风险阈值
    
    # 概率评分阈值
    high_prob_threshold: int = 75     # 高概率阈值
    medium_prob_threshold: int = 65   # 中概率阈值
    low_prob_threshold: int = 50      # 低概率阈值
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradingConfig":
        """从字典创建配置"""
        return cls(**data)
    
    def save(self, file_path: Optional[Path] = None) -> None:
        """保存配置到文件"""
        if file_path is None:
            file_path = Settings.USER_CONFIG_FILE
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, file_path: Optional[Path] = None) -> "TradingConfig":
        """从文件加载配置"""
        if file_path is None:
            file_path = Settings.USER_CONFIG_FILE
        
        if not file_path.exists():
            # 如果配置文件不存在，创建默认配置
            config = cls()
            config.save(file_path)
            return config
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def get_preset(cls, preset_name: str) -> "TradingConfig":
        """获取预设配置"""
        presets = {
            "conservative": cls(
                min_pct_chg=1.0,
                max_pct_chg=4.0,
                min_volume_ratio=1.1,
                max_volume_ratio=2.0,
                max_position_ratio=0.70,
                max_single_position=0.08,
                max_total_position=0.50,
                stop_loss_ratio=-0.03,
                take_profit_ratio=0.05,
                low_risk_threshold=30,
                medium_risk_threshold=50,
                high_risk_threshold=70
            ),
            "balanced": cls(
                min_pct_chg=1.0,
                max_pct_chg=6.0,
                min_volume_ratio=1.1,
                max_volume_ratio=3.0,
                max_position_ratio=0.85,
                max_single_position=0.10,
                max_total_position=0.70,
                stop_loss_ratio=-0.05,
                take_profit_ratio=0.08,
                low_risk_threshold=40,
                medium_risk_threshold=60,
                high_risk_threshold=80
            ),
            "aggressive": cls(
                min_pct_chg=2.0,
                max_pct_chg=8.0,
                min_volume_ratio=1.5,
                max_volume_ratio=4.0,
                max_position_ratio=0.95,
                max_single_position=0.15,
                max_total_position=0.90,
                stop_loss_ratio=-0.08,
                take_profit_ratio=0.12,
                low_risk_threshold=50,
                medium_risk_threshold=70,
                high_risk_threshold=90
            )
        }
        
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")
        
        return presets[preset_name]
    
    @classmethod
    def get_available_presets(cls) -> Dict[str, str]:
        """获取可用的预设配置"""
        return {
            "conservative": "保守型 - 低风险低收益",
            "balanced": "平衡型 - 中风险中收益",
            "aggressive": "激进型 - 高风险高收益"
        }
