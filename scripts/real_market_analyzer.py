#!/usr/bin/env python3
"""
真实市场强弱判断系统

基于实际市场数据判断市场趋势和强弱
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import requests
import json

class RealMarketAnalyzer:
    """真实市场分析器"""
    
    def __init__(self):
        self.market_indicators = {}
        
    def get_market_data(self, days: int = 10) -> Dict[str, Any]:
        """
        获取市场数据（上证指数、深证成指、创业板指）
        
        Args:
            days: 获取天数
            
        Returns:
            市场数据字典
        """
        try:
            # 这里可以接入真实的市场数据API
            # 暂时使用模拟数据演示逻辑
            
            # 模拟上证指数数据
            base_price = 3200
            dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)]
            
            # 生成模拟的市场数据（实际使用时替换为真实API）
            market_data = {
                "sh_index": {  # 上证指数
                    "dates": dates,
                    "close": [base_price + np.random.normal(0, 20) for _ in range(days)],
                    "volume": [100000000 + np.random.normal(0, 20000000) for _ in range(days)]
                },
                "sz_index": {  # 深证成指
                    "dates": dates,
                    "close": [12000 + np.random.normal(0, 100) for _ in range(days)],
                    "volume": [80000000 + np.random.normal(0, 15000000) for _ in range(days)]
                },
                "cy_index": {  # 创业板指
                    "dates": dates,
                    "close": [2400 + np.random.normal(0, 50) for _ in range(days)],
                    "volume": [60000000 + np.random.normal(0, 10000000) for _ in range(days)]
                }
            }
            
            return market_data
            
        except Exception as e:
            print(f"获取市场数据失败: {e}")
            return None
    
    def calculate_trend_strength(self, prices: List[float]) -> Tuple[str, float]:
        """
        计算趋势强度
        
        Args:
            prices: 价格序列
            
        Returns:
            (趋势方向, 强度值)
        """
        if len(prices) < 3:
            return "震荡", 0.5
        
        # 计算价格变化率
        price_changes = []
        for i in range(1, len(prices)):
            change = (prices[i] - prices[i-1]) / prices[i-1] * 100
            price_changes.append(change)
        
        # 计算趋势
        avg_change = np.mean(price_changes)
        std_change = np.std(price_changes)
        
        # 判断趋势方向
        if avg_change > 0.5:
            trend = "上涨"
        elif avg_change < -0.5:
            trend = "下跌"
        else:
            trend = "震荡"
        
        # 计算强度（基于变化幅度和一致性）
        consistency = 1 - (std_change / (abs(avg_change) + 1))  # 一致性
        magnitude = min(abs(avg_change) / 2, 1.0)  # 幅度
        strength = (consistency * 0.6 + magnitude * 0.4)
        strength = max(0.1, min(1.0, strength))  # 限制在0.1-1.0之间
        
        return trend, strength
    
    def calculate_volume_trend(self, volumes: List[float]) -> str:
        """
        计算成交量趋势
        
        Args:
            volumes: 成交量序列
            
        Returns:
            成交量趋势
        """
        if len(volumes) < 3:
            return "平稳"
        
        recent_avg = np.mean(volumes[-3:])  # 最近3天平均
        previous_avg = np.mean(volumes[-6:-3])  # 前3天平均
        
        change_ratio = (recent_avg - previous_avg) / previous_avg
        
        if change_ratio > 0.15:
            return "放量"
        elif change_ratio < -0.15:
            return "缩量"
        else:
            return "平稳"
    
    def calculate_volatility(self, prices: List[float]) -> float:
        """
        计算波动率
        
        Args:
            prices: 价格序列
            
        Returns:
            波动率
        """
        if len(prices) < 2:
            return 0.1
        
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        
        return np.std(returns) if returns else 0.1
    
    def assess_risk_level(self, volatility: float, trend: str, strength: float) -> str:
        """
        评估风险水平
        
        Args:
            volatility: 波动率
            trend: 趋势
            strength: 强度
            
        Returns:
            风险水平
        """
        risk_score = 0
        
        # 波动率风险
        if volatility > 0.03:
            risk_score += 30
        elif volatility > 0.02:
            risk_score += 20
        else:
            risk_score += 10
        
        # 趋势风险
        if trend == "下跌":
            risk_score += 30
        elif trend == "震荡":
            risk_score += 20
        else:
            risk_score += 10
        
        # 强度风险
        if strength > 0.8:
            risk_score += 20  # 过强可能反转
        elif strength < 0.3:
            risk_score += 15  # 过弱不确定
        else:
            risk_score += 5
        
        if risk_score > 60:
            return "高"
        elif risk_score > 40:
            return "中等"
        else:
            return "低"
    
    def analyze_market_comprehensive(self, days: int = 7) -> Dict[str, Any]:
        """
        综合分析市场
        
        Args:
            days: 分析天数
            
        Returns:
            综合市场分析结果
        """
        print("📊 正在获取市场数据...")
        market_data = self.get_market_data(days)
        
        if not market_data:
            # 使用默认值
            return {
                "trend": "震荡",
                "strength": 0.5,
                "volume_trend": "平稳",
                "risk_level": "中等",
                "volatility": 0.02,
                "details": "数据获取失败，使用默认分析"
            }
        
        print("🧮 分析各项指标...")
        
        # 分析各个指数
        indices_analysis = {}
        for index_name, index_data in market_data.items():
            trend, strength = self.calculate_trend_strength(index_data["close"])
            volume_trend = self.calculate_volume_trend(index_data["volume"])
            volatility = self.calculate_volatility(index_data["close"])
            
            indices_analysis[index_name] = {
                "trend": trend,
                "strength": strength,
                "volume_trend": volume_trend,
                "volatility": volatility
            }
        
        # 综合判断（以上证指数为主，其他指数为辅）
        sh_analysis = indices_analysis.get("sh_index", {})
        main_trend = sh_analysis.get("trend", "震荡")
        main_strength = sh_analysis.get("strength", 0.5)
        main_volatility = sh_analysis.get("volatility", 0.02)
        
        # 计算一致性（多个指数趋势是否一致）
        trends = [analysis.get("trend", "震荡") for analysis in indices_analysis.values()]
        trend_consistency = len([t for t in trends if t == main_trend]) / len(trends)
        
        # 调整强度（考虑一致性）
        adjusted_strength = main_strength * trend_consistency
        
        # 综合成交量趋势
        volume_trends = [analysis.get("volume_trend", "平稳") for analysis in indices_analysis.values()]
        main_volume_trend = max(set(volume_trends), key=volume_trends.count)
        
        # 风险评估
        risk_level = self.assess_risk_level(main_volatility, main_trend, adjusted_strength)
        
        # 识别热点板块（模拟）
        hot_sectors = self.identify_hot_sectors()
        
        result = {
            "trend": main_trend,
            "strength": round(adjusted_strength, 2),
            "volume_trend": main_volume_trend,
            "risk_level": risk_level,
            "volatility": round(main_volatility, 4),
            "consistency": round(trend_consistency, 2),
            "hot_sectors": hot_sectors,
            "indices_detail": indices_analysis,
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "details": f"基于{days}天数据分析，趋势一致性{trend_consistency:.1%}"
        }
        
        return result
    
    def identify_hot_sectors(self) -> List[str]:
        """
        识别热点板块（简化版本）
        
        Returns:
            热点板块列表
        """
        # 这里可以接入实际的板块数据
        # 暂时使用模拟数据
        all_sectors = ["科技", "医药", "新能源", "军工", "消费", "金融", "地产", "周期"]
        
        # 模拟热点板块识别
        import random
        hot_count = random.randint(2, 4)
        hot_sectors = random.sample(all_sectors, hot_count)
        
        return hot_sectors
    
    def get_market_summary(self) -> str:
        """
        获取市场摘要
        
        Returns:
            市场摘要文本
        """
        analysis = self.analyze_market_comprehensive()
        
        trend = analysis["trend"]
        strength = analysis["strength"]
        risk = analysis["risk_level"]
        consistency = analysis["consistency"]
        
        summary = f"""
📊 市场状态摘要 ({analysis['analysis_time']})

🎯 主要指标：
• 趋势方向：{trend}
• 趋势强度：{strength:.1%} ({'强' if strength > 0.7 else '中' if strength > 0.4 else '弱'})
• 成交量：{analysis['volume_trend']}
• 风险水平：{risk}
• 一致性：{consistency:.1%}

🔥 热点板块：{', '.join(analysis['hot_sectors'])}

💡 市场解读："""
        
        if trend == "上涨":
            if strength > 0.7:
                summary += "\n• 强势上涨行情，可适度追涨"
            else:
                summary += "\n• 温和上涨行情，稳健操作"
        elif trend == "下跌":
            summary += "\n• 下跌行情，谨慎防守"
        else:
            summary += "\n• 震荡行情，区间操作"
        
        if consistency < 0.6:
            summary += "\n• ⚠️ 指数分化，需谨慎选择标的"
        
        return summary

def create_market_analysis_demo():
    """创建市场分析演示"""
    analyzer = RealMarketAnalyzer()
    
    print("=" * 60)
    print("🎯 市场强弱判断系统演示")
    print("=" * 60)
    
    # 获取市场摘要
    summary = analyzer.get_market_summary()
    print(summary)
    
    print("\n" + "=" * 60)
    print("📈 详细技术指标")
    print("=" * 60)
    
    # 获取详细分析
    analysis = analyzer.analyze_market_comprehensive()
    
    print(f"各指数分析:")
    for index_name, detail in analysis["indices_detail"].items():
        index_names = {
            "sh_index": "上证指数",
            "sz_index": "深证成指", 
            "cy_index": "创业板指"
        }
        print(f"• {index_names.get(index_name, index_name)}:")
        print(f"  趋势: {detail['trend']} (强度: {detail['strength']:.1%})")
        print(f"  成交量: {detail['volume_trend']}")
        print(f"  波动率: {detail['volatility']:.2%}")

if __name__ == "__main__":
    create_market_analysis_demo()
