#!/usr/bin/env python3
"""
连涨回调策略

专门针对连续上涨股票的回调介入策略
在股票回调到支撑位时寻找最佳尾盘介入时机
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from tail_trading.strategies.tail_up_strategy import TailUpStrategy
    from tail_trading.config.trading_config import TradingConfig
    from tail_trading.data.eastmoney.daily_fetcher import EastmoneyDataFetcher
    from scripts.consecutive_rise_analyzer import ConsecutiveRiseAnalyzer
except ImportError:
    print("⚠️ 无法导入部分模块，使用基础分析模式")

class RetracementTailStrategy:
    """回调尾盘策略"""
    
    def __init__(self):
        try:
            self.data_fetcher = EastmoneyDataFetcher()
            self.risk_analyzer = ConsecutiveRiseAnalyzer()
            self.base_strategy = TailUpStrategy()
        except:
            print("⚠️ 模块初始化警告，部分功能可能受限")
            self.data_fetcher = None
            self.risk_analyzer = None
            self.base_strategy = None
    
    def should_avoid_stock(self, code: str) -> Tuple[bool, str]:
        """
        判断是否应该避免这只股票
        
        Args:
            code: 股票代码
            
        Returns:
            (是否避免, 原因)
        """
        if not self.risk_analyzer:
            return False, "风险分析器未初始化"
        
        try:
            analysis = self.risk_analyzer.analyze_retracement_opportunity(code)
            
            if "error" in analysis:
                return True, f"数据获取失败: {analysis['error']}"
            
            consecutive = analysis["连续分析"]
            rise_days = consecutive["current_consecutive_rise"]
            risk_level = consecutive["risk_level"]
            
            # 连涨超过4天，坚决避免
            if rise_days >= 4:
                return True, f"连涨{rise_days}天，回调风险极大"
            
            # 连涨3天且在高位，避免
            position_ratio = analysis["支撑分析"]["position_ratio"]
            if rise_days >= 3 and position_ratio > 70:
                return True, f"连涨{rise_days}天且处于高位({position_ratio:.1f}%)"
            
            # 当日涨幅过大（超过7%），避免追高
            today_change = analysis["今日涨跌幅"]
            if today_change > 7:
                return True, f"当日涨幅过大({today_change:.1f}%)"
            
            return False, "风险可控"
            
        except Exception as e:
            return True, f"分析出错: {str(e)}"
    
    def find_retracement_candidates(self, stock_pool: List[str]) -> List[Dict[str, Any]]:
        """
        从股票池中找出适合回调介入的候选股票
        
        Args:
            stock_pool: 股票代码列表
            
        Returns:
            候选股票列表（按优先级排序）
        """
        candidates = []
        
        print(f"🔍 正在筛选回调介入机会 (共{len(stock_pool)}只股票)...")
        
        for i, code in enumerate(stock_pool, 1):
            print(f"📊 进度: {i}/{len(stock_pool)} - 分析 {code}")
            
            # 检查是否应该避免
            should_avoid, avoid_reason = self.should_avoid_stock(code)
            if should_avoid:
                print(f"⚠️ {code} - 跳过: {avoid_reason}")
                continue
            
            # 详细分析
            if self.risk_analyzer:
                analysis = self.risk_analyzer.analyze_retracement_opportunity(code)
                
                if "error" not in analysis:
                    score = self._calculate_retracement_score(analysis)
                    
                    candidate = {
                        "代码": code,
                        "名称": analysis.get("名称", ""),
                        "当前价格": analysis["当前价格"],
                        "今日涨跌幅": analysis["今日涨跌幅"],
                        "连涨天数": analysis["连续分析"]["current_consecutive_rise"],
                        "风险等级": analysis["连续分析"]["risk_level"],
                        "位置评估": analysis["支撑分析"]["current_position"],
                        "操作建议": analysis["操作建议"]["操作建议"],
                        "介入时机": analysis["操作建议"]["介入时机"],
                        "综合评分": score,
                        "详细分析": analysis
                    }
                    
                    candidates.append(candidate)
                    print(f"✅ {code} - 评分: {score:.1f}")
        
        # 按评分排序
        candidates.sort(key=lambda x: x["综合评分"], reverse=True)
        
        return candidates
    
    def _calculate_retracement_score(self, analysis: Dict[str, Any]) -> float:
        """
        计算回调介入评分
        
        Args:
            analysis: 股票分析结果
            
        Returns:
            评分（0-100）
        """
        score = 50.0  # 基础分
        
        consecutive = analysis["连续分析"]
        support = analysis["支撑分析"]
        recommendation = analysis["操作建议"]
        
        rise_days = consecutive["current_consecutive_rise"]
        fall_days = consecutive["current_consecutive_fall"]
        position_ratio = support["position_ratio"]
        today_change = analysis["今日涨跌幅"]
        
        # 连涨天数评分（适度连涨加分，过度连涨减分）
        if rise_days == 0:
            score += 5  # 没有连涨，稳定
        elif rise_days == 1:
            score += 10  # 1天涨，温和
        elif rise_days == 2:
            score += 15  # 2天涨，较好
        elif rise_days == 3:
            score += 5   # 3天涨，开始有风险
        else:
            score -= 20  # 超过3天，风险大
        
        # 连跌天数评分（回调机会）
        if fall_days >= 2:
            score += 20  # 连续下跌，可能反弹
        elif fall_days == 1:
            score += 10  # 1天下跌，小回调
        
        # 位置评分（低位加分，高位减分）
        if position_ratio < 30:
            score += 20  # 低位，安全
        elif position_ratio < 50:
            score += 10  # 中低位，较好
        elif position_ratio < 70:
            score += 0   # 中高位，一般
        else:
            score -= 15  # 高位，风险大
        
        # 当日涨跌幅评分
        if -3 <= today_change <= -1:
            score += 15  # 小幅回调，理想
        elif -5 <= today_change < -3:
            score += 10  # 中等回调，可以
        elif today_change < -5:
            score += 5   # 大幅下跌，谨慎
        elif 0 <= today_change <= 2:
            score += 5   # 微涨，温和
        elif 2 < today_change <= 5:
            score -= 5   # 中等上涨，小心
        else:
            score -= 15  # 大涨，风险大
        
        # 操作建议评分
        action = recommendation["操作建议"]
        if action == "积极关注":
            score += 20
        elif action == "可适量关注":
            score += 10
        elif action == "正常评估":
            score += 0
        elif action == "谨慎观望":
            score -= 10
        elif action == "避免介入":
            score -= 30
        
        # 确保评分在合理范围内
        return max(0, min(100, score))
    
    def execute_tail_selection(self, candidates: List[Dict[str, Any]], max_stocks: int = 5) -> List[Dict[str, Any]]:
        """
        执行尾盘选股
        
        Args:
            candidates: 候选股票列表
            max_stocks: 最大选股数量
            
        Returns:
            最终选股结果
        """
        if not candidates:
            print("❌ 没有合适的候选股票")
            return []
        
        print(f"\n🎯 尾盘选股 - 从{len(candidates)}只候选股票中选择前{max_stocks}只")
        
        # 取前N只高评分股票
        selected = candidates[:max_stocks]
        
        # 进一步尾盘分析
        final_selections = []
        
        for stock in selected:
            code = stock["代码"]
            
            # 获取实时数据做最终判断
            tail_analysis = self._analyze_tail_opportunity(stock)
            
            stock["尾盘分析"] = tail_analysis
            stock["最终建议"] = tail_analysis["建议"]
            
            if tail_analysis["建议"] != "放弃":
                final_selections.append(stock)
        
        return final_selections
    
    def _analyze_tail_opportunity(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析尾盘介入机会
        
        Args:
            stock: 股票信息
            
        Returns:
            尾盘分析结果
        """
        code = stock["代码"]
        current_time = datetime.now()
        
        # 简化版尾盘分析（实际应该获取实时数据）
        score = stock["综合评分"]
        today_change = stock["今日涨跌幅"]
        position = stock["位置评估"]
        
        # 基于时间的建议
        if current_time.hour < 14:
            timing = "等待尾盘"
        elif current_time.hour == 14:
            timing = "尾盘观察期"
        else:
            timing = "尾盘介入期"
        
        # 基于评分的建议
        if score >= 80:
            suggestion = "重点关注"
        elif score >= 70:
            suggestion = "积极考虑"
        elif score >= 60:
            suggestion = "可以关注"
        elif score >= 50:
            suggestion = "谨慎考虑"
        else:
            suggestion = "放弃"
        
        # 具体操作策略
        if suggestion != "放弃":
            if today_change < -2:
                strategy = "回调买入 - 可在收盘前30分钟关注"
            elif today_change > 3:
                strategy = "避免追高 - 等待回调"
            else:
                strategy = "正常操作 - 尾盘15分钟内观察"
        else:
            strategy = "今日不操作"
        
        return {
            "时机": timing,
            "建议": suggestion,
            "策略": strategy,
            "理由": f"评分{score:.1f}, 今日{today_change:.1f}%, {position}"
        }

def main():
    """主函数"""
    print("🎯 连涨回调尾盘策略")
    print("=" * 50)
    
    strategy = RetracementTailStrategy()
    
    # 示例股票池（实际使用时应该从选股系统获取）
    sample_pool = [
        "000001", "000002", "000858", "000876", "002001",
        "002027", "002120", "002415", "300001", "300122",
        "600001", "600036", "600519", "600887", "601318"
    ]
    
    print(f"\n📊 分析股票池: {len(sample_pool)} 只股票")
    
    try:
        # 1. 筛选候选股票
        candidates = strategy.find_retracement_candidates(sample_pool)
        
        if not candidates:
            print("\n❌ 未找到合适的回调介入机会")
            return
        
        print(f"\n✅ 找到 {len(candidates)} 只候选股票")
        print("\n📋 候选股票排行榜:")
        print("-" * 80)
        
        for i, stock in enumerate(candidates[:10], 1):  # 显示前10只
            print(f"{i:2d}. {stock['代码']} {stock['名称']:8s} "
                  f"评分:{stock['综合评分']:5.1f} "
                  f"连涨:{stock['连涨天数']}天 "
                  f"今日:{stock['今日涨跌幅']:+5.1f}% "
                  f"{stock['操作建议']}")
        
        # 2. 执行尾盘选股
        final_selections = strategy.execute_tail_selection(candidates, max_stocks=5)
        
        if final_selections:
            print(f"\n🎯 最终尾盘选股结果 ({len(final_selections)} 只):")
            print("=" * 60)
            
            for i, stock in enumerate(final_selections, 1):
                tail_info = stock["尾盘分析"]
                print(f"\n{i}. {stock['代码']} {stock['名称']}")
                print(f"   💰 当前价格: {stock['当前价格']:.2f}元")
                print(f"   📈 今日涨跌: {stock['今日涨跌幅']:+.2f}%")
                print(f"   ⭐ 综合评分: {stock['综合评分']:.1f}分")
                print(f"   🎯 尾盘建议: {tail_info['建议']}")
                print(f"   📋 操作策略: {tail_info['策略']}")
                print(f"   💡 建议理由: {tail_info['理由']}")
        else:
            print("\n❌ 尾盘分析后，暂无推荐股票")
        
        # 3. 风险提醒
        print(f"\n⚠️ 风险提醒:")
        print("1. 连涨股票存在回调风险，严格控制仓位")
        print("2. 等待回调到支撑位再介入，避免追高")
        print("3. 尾盘15分钟内观察成交量和价格走势")
        print("4. 设置止损位，及时止盈止损")
        
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
