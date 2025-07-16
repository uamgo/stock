"""
风险管理器

提供风险评估、风险控制和风险监控功能
"""

from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from dataclasses import dataclass

from ..config.trading_config import TradingConfig
from ..config.logging_config import get_logger

@dataclass
class RiskMetrics:
    """风险指标"""
    total_risk_score: float
    position_risk: float
    volume_risk: float
    technical_risk: float
    timing_risk: float
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    warning_messages: List[str]

class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: TradingConfig = None):
        """
        初始化风险管理器
        
        Args:
            config: 交易配置
        """
        self.config = config or TradingConfig()
        self.logger = get_logger("risk_manager")
    
    def assess_stock_risk(self, stock_data: Dict[str, Any]) -> RiskMetrics:
        """
        评估单只股票的风险
        
        Args:
            stock_data: 股票数据
            
        Returns:
            风险指标
        """
        warnings = []
        
        # 1. 位置风险评估
        position_ratio = stock_data.get('position_ratio', 0)
        if position_ratio > 0.8:
            position_risk = 30
            warnings.append("股价位置偏高，存在高位接盘风险")
        elif position_ratio > 0.6:
            position_risk = 15
            warnings.append("股价位置较高，需要关注")
        else:
            position_risk = 0
        
        # 2. 成交量风险评估
        volume_ratio = stock_data.get('volume_ratio', 0)
        if volume_ratio > 3.0:
            volume_risk = 25
            warnings.append("成交量过度放大，可能存在炒作风险")
        elif volume_ratio > 2.5:
            volume_risk = 15
            warnings.append("成交量较大，需要谨慎")
        elif volume_ratio < 1.1:
            volume_risk = 10
            warnings.append("成交量不足，流动性风险")
        else:
            volume_risk = 0
        
        # 3. 技术形态风险评估
        upper_shadow = stock_data.get('upper_shadow', 0)
        body_length = stock_data.get('body_length', 1)
        lower_shadow = stock_data.get('lower_shadow', 0)
        
        technical_risk = 0
        if upper_shadow > body_length * 0.5:
            technical_risk += 15
            warnings.append("上影线过长，存在抛压风险")
        
        if lower_shadow < body_length * 0.1:
            technical_risk += 10
            warnings.append("下影线过短，支撑力度不足")
        
        # 4. 时间风险评估
        timing_risk = self._assess_timing_risk()
        if timing_risk > 0:
            warnings.append("当前时间段存在额外风险")
        
        # 计算总风险评分
        total_risk = position_risk + volume_risk + technical_risk + timing_risk
        
        # 确定风险等级
        if total_risk <= self.config.low_risk_threshold:
            risk_level = "LOW"
        elif total_risk <= self.config.medium_risk_threshold:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return RiskMetrics(
            total_risk_score=total_risk,
            position_risk=position_risk,
            volume_risk=volume_risk,
            technical_risk=technical_risk,
            timing_risk=timing_risk,
            risk_level=risk_level,
            warning_messages=warnings
        )
    
    def _assess_timing_risk(self) -> float:
        """
        评估时间风险
        
        Returns:
            时间风险评分
        """
        now = datetime.now()
        weekday = now.weekday()
        
        # 周五风险
        if weekday == 4:
            return 10
        
        # 周末风险
        if weekday in [5, 6]:
            return 20
        
        return 0
    
    def check_position_limits(self, current_positions: Dict[str, float], 
                            new_position: str, position_size: float) -> tuple[bool, str]:
        """
        检查仓位限制
        
        Args:
            current_positions: 当前持仓 {股票代码: 仓位比例}
            new_position: 新仓位股票代码
            position_size: 新仓位大小
            
        Returns:
            (是否允许, 原因)
        """
        # 检查单只股票仓位限制
        current_stock_position = current_positions.get(new_position, 0)
        total_stock_position = current_stock_position + position_size
        
        if total_stock_position > self.config.max_single_position:
            return False, f"超过单只股票最大仓位限制 {self.config.max_single_position*100:.1f}%"
        
        # 检查总仓位限制
        total_position = sum(current_positions.values()) + position_size
        if total_position > self.config.max_total_position:
            return False, f"超过总仓位限制 {self.config.max_total_position*100:.1f}%"
        
        return True, "仓位检查通过"
    
    def should_stop_loss(self, buy_price: float, current_price: float) -> bool:
        """
        判断是否应该止损
        
        Args:
            buy_price: 买入价格
            current_price: 当前价格
            
        Returns:
            是否应该止损
        """
        loss_ratio = (current_price - buy_price) / buy_price
        return loss_ratio <= self.config.stop_loss_ratio
    
    def should_take_profit(self, buy_price: float, current_price: float) -> bool:
        """
        判断是否应该止盈
        
        Args:
            buy_price: 买入价格
            current_price: 当前价格
            
        Returns:
            是否应该止盈
        """
        profit_ratio = (current_price - buy_price) / buy_price
        return profit_ratio >= self.config.take_profit_ratio
    
    def assess_portfolio_risk(self, positions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估投资组合风险
        
        Args:
            positions: 持仓信息
            
        Returns:
            组合风险评估
        """
        if not positions:
            return {
                "total_risk_score": 0,
                "risk_level": "LOW",
                "diversification_score": 100,
                "concentration_risk": 0,
                "warnings": []
            }
        
        warnings = []
        
        # 计算集中度风险
        position_sizes = [pos.get('position_size', 0) for pos in positions.values()]
        max_position = max(position_sizes)
        
        if max_position > 0.2:
            concentration_risk = 30
            warnings.append("持仓过于集中，存在集中度风险")
        elif max_position > 0.15:
            concentration_risk = 15
            warnings.append("持仓集中度较高")
        else:
            concentration_risk = 0
        
        # 计算分散化评分
        num_positions = len(positions)
        if num_positions < 3:
            diversification_score = 60
            warnings.append("持仓数量较少，分散化不足")
        elif num_positions < 5:
            diversification_score = 80
        else:
            diversification_score = 100
        
        # 计算平均风险评分
        individual_risks = []
        for code, position in positions.items():
            risk_metrics = self.assess_stock_risk(position)
            individual_risks.append(risk_metrics.total_risk_score)
        
        avg_risk = sum(individual_risks) / len(individual_risks) if individual_risks else 0
        
        # 总风险评分
        total_risk = (avg_risk + concentration_risk) * (1 - diversification_score / 100)
        
        # 风险等级
        if total_risk <= 30:
            risk_level = "LOW"
        elif total_risk <= 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return {
            "total_risk_score": total_risk,
            "risk_level": risk_level,
            "diversification_score": diversification_score,
            "concentration_risk": concentration_risk,
            "average_individual_risk": avg_risk,
            "num_positions": num_positions,
            "warnings": warnings
        }
    
    def get_risk_report(self, stock_data: Dict[str, Any]) -> str:
        """
        生成风险报告
        
        Args:
            stock_data: 股票数据
            
        Returns:
            风险报告文本
        """
        risk_metrics = self.assess_stock_risk(stock_data)
        
        report = f"""
=== 风险评估报告 ===
股票代码: {stock_data.get('code', 'N/A')}
股票名称: {stock_data.get('name', 'N/A')}

总风险评分: {risk_metrics.total_risk_score:.1f}分
风险等级: {risk_metrics.risk_level}

风险分解:
- 位置风险: {risk_metrics.position_risk:.1f}分
- 成交量风险: {risk_metrics.volume_risk:.1f}分
- 技术形态风险: {risk_metrics.technical_risk:.1f}分
- 时间风险: {risk_metrics.timing_risk:.1f}分

风险提示:
"""
        
        for warning in risk_metrics.warning_messages:
            report += f"- {warning}\n"
        
        return report
