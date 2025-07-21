#!/usr/bin/env python3
"""
市场适应性选股策略

根据市场环境调整选股策略，提高与市场的匹配度
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import json
from pathlib import Path
from .real_market_analyzer import RealMarketAnalyzer

class MarketAdaptiveStrategy:
    """市场适应性选股策略"""
    
    def __init__(self):
        self.market_indicators = {}
        self.strategy_weights = {}
        self.market_analyzer = RealMarketAnalyzer()
        
    def analyze_market_trend(self, days: int = 5) -> Dict[str, Any]:
        """
        分析市场趋势（使用真实市场数据）
        
        Args:
            days: 分析天数
            
        Returns:
            市场分析结果
        """
        return self.market_analyzer.analyze_market_comprehensive(days)
    
    def get_adaptive_config(self, market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据市场环境获取适应性配置
        
        Args:
            market_analysis: 市场分析结果
            
        Returns:
            适应性配置
        """
        trend = market_analysis.get("trend", "震荡")
        strength = market_analysis.get("strength", 0.5)
        risk_level = market_analysis.get("risk_level", "中等")
        
        config = {}
        
        # 根据市场趋势调整选股参数
        if trend == "上涨":
            if strength > 0.7:
                # 强势上涨市场
                config.update({
                    "stock_count": 3,  # 选股数量
                    "min_prob_score": 15,  # 降低门槛，跟上市场
                    "position_ratio_weight": 0.1,  # 降低位置权重
                    "trend_weight": 0.4,  # 提高趋势权重
                    "diversify": True,  # 分散持股
                    "strategy_type": "趋势跟随"
                })
            else:
                # 温和上涨市场
                config.update({
                    "stock_count": 2,
                    "min_prob_score": 20,
                    "position_ratio_weight": 0.2,
                    "trend_weight": 0.3,
                    "diversify": True,
                    "strategy_type": "稳健跟随"
                })
        elif trend == "下跌":
            # 下跌市场
            config.update({
                "stock_count": 1,  # 减少持仓
                "min_prob_score": 25,  # 提高门槛
                "position_ratio_weight": 0.3,  # 重视位置
                "trend_weight": 0.2,
                "diversify": False,  # 精选个股
                "strategy_type": "防守反击"
            })
        else:
            # 震荡市场
            config.update({
                "stock_count": 2,
                "min_prob_score": 22,
                "position_ratio_weight": 0.25,
                "trend_weight": 0.25,
                "diversify": True,
                "strategy_type": "波段操作"
            })
        
        # 根据风险水平调整
        if risk_level == "高":
            config["min_prob_score"] += 5
            config["stock_count"] = max(1, config["stock_count"] - 1)
        elif risk_level == "低":
            config["min_prob_score"] -= 3
            config["stock_count"] += 1
        
        return config
    
    def select_adaptive_stocks(self, selected_stocks: pd.DataFrame, 
                             market_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据市场环境自适应选股
        
        Args:
            selected_stocks: 候选股票
            market_analysis: 市场分析
            
        Returns:
            最终选择的股票列表
        """
        if selected_stocks.empty:
            return []
        
        config = self.get_adaptive_config(market_analysis)
        
        # 过滤评分过低的股票
        min_score = config["min_prob_score"]
        qualified_stocks = selected_stocks[
            selected_stocks["次日补涨概率"] >= min_score
        ].copy()
        
        if qualified_stocks.empty:
            print(f"⚠️ 没有股票评分超过 {min_score} 分，建议今日观望")
            return []
        
        # 根据策略类型调整选股逻辑
        strategy_type = config["strategy_type"]
        stock_count = min(config["stock_count"], len(qualified_stocks))
        
        if strategy_type == "趋势跟随":
            # 强趋势市场：选择涨幅较大但不过热的股票
            result = qualified_stocks[
                (qualified_stocks["涨跌幅"] >= 2.0) & 
                (qualified_stocks["涨跌幅"] <= 5.0)
            ].head(stock_count)
            
        elif strategy_type == "防守反击":
            # 下跌市场：选择位置较低、风险较小的股票
            result = qualified_stocks[
                qualified_stocks["20日位置"] <= 70
            ].nsmallest(stock_count, "风险评分")
            
        elif strategy_type == "波段操作":
            # 震荡市场：平衡各项指标
            result = qualified_stocks.head(stock_count)
            
        else:
            # 默认选择评分最高的
            result = qualified_stocks.head(stock_count)
        
        # 如果需要分散投资，避免同板块过度集中
        if config.get("diversify", False) and len(result) > 1:
            result = self._diversify_selection(result)
        
        return result.to_dict('records')
    
    def _diversify_selection(self, stocks: pd.DataFrame) -> pd.DataFrame:
        """
        分散化选股，避免集中在同一板块
        
        Args:
            stocks: 候选股票
            
        Returns:
            分散化后的股票
        """
        # 这里可以根据实际的板块信息进行分散化
        # 暂时按照股票代码分散（简化处理）
        diversified = []
        used_prefixes = set()
        
        for _, stock in stocks.iterrows():
            code = stock["代码"]
            prefix = code[:3]  # 取前3位作为板块标识
            
            if prefix not in used_prefixes or len(diversified) == 0:
                diversified.append(stock)
                used_prefixes.add(prefix)
            
            if len(diversified) >= 3:  # 最多选3只
                break
        
        return pd.DataFrame(diversified)
    
    def generate_trading_advice(self, selected_stocks: List[Dict[str, Any]], 
                              market_analysis: Dict[str, Any]) -> str:
        """
        生成交易建议
        
        Args:
            selected_stocks: 选中的股票
            market_analysis: 市场分析
            
        Returns:
            交易建议文本
        """
        if not selected_stocks:
            return "❌ 当前市场环境下建议观望，没有合适的投资标的。"
        
        trend = market_analysis.get("trend", "震荡")
        strategy_type = self.get_adaptive_config(market_analysis)["strategy_type"]
        
        advice = f"""
🎯 市场适应性交易建议

📊 市场环境：{trend}市场 ({strategy_type})
🎲 选股数量：{len(selected_stocks)}只

📋 推荐股票："""
        
        for i, stock in enumerate(selected_stocks, 1):
            advice += f"""
{i}. {stock['代码']} {stock.get('名称', '')}
   评分：{stock['次日补涨概率']:.1f}分 | 涨幅：{stock['涨跌幅']:.2f}% | 位置：{stock['20日位置']:.1f}%"""
        
        advice += f"""

💡 操作建议：
"""
        
        if trend == "上涨":
            advice += """- 🚀 顺势而为，适当追涨但控制仓位
- ⚡ 快进快出，及时止盈
- 📈 关注量能配合"""
        elif trend == "下跌":
            advice += """- 🛡️ 轻仓试水，严格止损
- 🎯 选择低位优质股
- ⏰ 耐心等待反弹信号"""
        else:
            advice += """- ⚖️ 波段操作，高抛低吸
- 🔄 灵活调仓，快速应变
- 📊 关注技术形态"""
        
        advice += f"""
- 💰 单只仓位建议：不超过总资金的10%
- 📉 止损位：-5%
- 📈 止盈位：+8%

⚠️ 风险提示：以上建议仅供参考，投资有风险，入市需谨慎！
"""
        
        return advice.strip()

def create_market_adaptive_selection_script():
    """创建市场适应性选股脚本"""
    script_content = '''#!/usr/bin/env python3
"""
智能选股脚本 - 市场适应性版本

根据市场环境自动调整选股策略
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.market_adaptive_strategy import MarketAdaptiveStrategy
from tail_trading.strategies.tail_up_strategy import TailUpStrategy
from tail_trading.config.trading_config import TradingConfig

def main():
    print("🤖 启动智能选股系统...")
    
    # 1. 分析市场环境
    print("📊 分析市场环境...")
    adaptive_strategy = MarketAdaptiveStrategy()
    market_analysis = adaptive_strategy.analyze_market_trend()
    
    print(f"市场趋势：{market_analysis['trend']}")
    print(f"趋势强度：{market_analysis['strength']:.1%}")
    print(f"风险水平：{market_analysis['risk_level']}")
    
    # 2. 获取适应性配置
    config = adaptive_strategy.get_adaptive_config(market_analysis)
    print(f"策略类型：{config['strategy_type']}")
    print(f"目标选股数量：{config['stock_count']}只")
    
    # 3. 执行基础选股
    print("\\n🔍 执行基础选股...")
    trading_config = TradingConfig.get_preset("balanced")
    strategy = TailUpStrategy(trading_config)
    
    all_stocks = strategy.select_stocks()
    print(f"基础筛选完成，共找到 {len(all_stocks)} 只候选股票")
    
    # 4. 市场适应性选股
    print("\\n🎯 应用市场适应性策略...")
    final_stocks = adaptive_strategy.select_adaptive_stocks(all_stocks, market_analysis)
    
    if not final_stocks:
        print("❌ 当前市场环境不适合操作，建议观望")
        return
    
    # 5. 生成交易建议
    advice = adaptive_strategy.generate_trading_advice(final_stocks, market_analysis)
    print(advice)
    
    # 6. 保存结果
    import json
    from datetime import datetime
    
    output_file = f"smart_selection_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    result = {
        "timestamp": datetime.now().isoformat(),
        "market_analysis": market_analysis,
        "adaptive_config": config,
        "selected_stocks": final_stocks,
        "advice": advice
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\\n💾 选股结果已保存到：{output_file}")

if __name__ == "__main__":
    main()
'''
    
    return script_content

if __name__ == "__main__":
    # 测试市场适应性策略
    strategy = MarketAdaptiveStrategy()
    
    # 模拟市场分析
    market_analysis = strategy.analyze_market_trend()
    print("市场分析结果：", market_analysis)
    
    # 获取适应性配置
    config = strategy.get_adaptive_config(market_analysis)
    print("适应性配置：", config)
