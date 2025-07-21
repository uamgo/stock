#!/usr/bin/env python3
"""
连涨风险分析系统

专门分析连续上涨股票的回调风险，寻找最佳介入时机
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
except ImportError:
    print("⚠️ 无法导入选股模块，使用独立分析模式")

class ConsecutiveRiseAnalyzer:
    """连涨风险分析器"""
    
    def __init__(self):
        try:
            self.data_fetcher = EastmoneyDataFetcher()
        except:
            self.data_fetcher = None
    
    def calculate_consecutive_days(self, daily_df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算连续涨跌天数
        
        Args:
            daily_df: 日线数据
            
        Returns:
            连续涨跌统计
        """
        if daily_df.empty or len(daily_df) < 5:
            return {"consecutive_rise": 0, "consecutive_fall": 0, "risk_level": "数据不足"}
        
        # 获取涨跌幅序列
        pct_changes = pd.to_numeric(daily_df["涨跌幅"], errors="coerce").fillna(0)
        
        # 计算连续上涨天数
        consecutive_rise = 0
        consecutive_fall = 0
        current_rise = 0
        current_fall = 0
        
        for pct in pct_changes[-10:]:  # 看最近10天
            if pct > 0:
                current_rise += 1
                current_fall = 0
            elif pct < 0:
                current_fall += 1
                current_rise = 0
            else:
                current_rise = 0
                current_fall = 0
            
            consecutive_rise = max(consecutive_rise, current_rise)
            consecutive_fall = max(consecutive_fall, current_fall)
        
        # 当前连续状态
        current_consecutive_rise = 0
        current_consecutive_fall = 0
        
        for pct in reversed(pct_changes[-10:]):
            if pct > 0:
                current_consecutive_rise += 1
            elif pct < 0:
                current_consecutive_fall += 1
            else:
                break
        
        # 风险评级
        risk_level = self._assess_consecutive_risk(current_consecutive_rise, current_consecutive_fall)
        
        return {
            "consecutive_rise": consecutive_rise,
            "consecutive_fall": consecutive_fall,
            "current_consecutive_rise": current_consecutive_rise,
            "current_consecutive_fall": current_consecutive_fall,
            "risk_level": risk_level,
            "recent_changes": pct_changes[-5:].tolist()
        }
    
    def _assess_consecutive_risk(self, rise_days: int, fall_days: int) -> str:
        """
        评估连续涨跌风险
        
        Args:
            rise_days: 连续上涨天数
            fall_days: 连续下跌天数
            
        Returns:
            风险等级
        """
        if rise_days >= 5:
            return "极高回调风险"
        elif rise_days >= 3:
            return "高回调风险"
        elif rise_days >= 2:
            return "中等回调风险"
        elif fall_days >= 3:
            return "超跌反弹机会"
        elif fall_days >= 2:
            return "可能见底"
        else:
            return "正常区间"
    
    def find_support_levels(self, daily_df: pd.DataFrame, days: int = 20) -> Dict[str, Any]:
        """
        寻找支撑位
        
        Args:
            daily_df: 日线数据
            days: 分析天数
            
        Returns:
            支撑位信息
        """
        if daily_df.empty or len(daily_df) < days:
            return {"supports": [], "current_position": "数据不足"}
        
        # 获取价格数据
        high_prices = pd.to_numeric(daily_df["最高"], errors="coerce").fillna(0)
        low_prices = pd.to_numeric(daily_df["最低"], errors="coerce").fillna(0)
        close_prices = pd.to_numeric(daily_df["收盘"], errors="coerce").fillna(0)
        
        recent_data = daily_df.tail(days)
        recent_lows = low_prices.tail(days)
        recent_highs = high_prices.tail(days)
        
        current_price = close_prices.iloc[-1]
        
        # 寻找支撑位（近期低点）
        supports = []
        
        # 1. 最近5日、10日、20日最低价
        supports.append({
            "type": "5日最低",
            "price": recent_lows.tail(5).min(),
            "distance": (current_price - recent_lows.tail(5).min()) / current_price * 100
        })
        
        supports.append({
            "type": "10日最低", 
            "price": recent_lows.tail(10).min(),
            "distance": (current_price - recent_lows.tail(10).min()) / current_price * 100
        })
        
        supports.append({
            "type": "20日最低",
            "price": recent_lows.tail(20).min(),
            "distance": (current_price - recent_lows.tail(20).min()) / current_price * 100
        })
        
        # 2. 重要均线支撑
        ma5 = close_prices.tail(20).rolling(5).mean().iloc[-1]
        ma10 = close_prices.tail(20).rolling(10).mean().iloc[-1]
        ma20 = close_prices.tail(20).rolling(20).mean().iloc[-1]
        
        supports.extend([
            {
                "type": "5日均线",
                "price": ma5,
                "distance": (current_price - ma5) / current_price * 100
            },
            {
                "type": "10日均线",
                "price": ma10,
                "distance": (current_price - ma10) / current_price * 100
            },
            {
                "type": "20日均线", 
                "price": ma20,
                "distance": (current_price - ma20) / current_price * 100
            }
        ])
        
        # 按距离排序
        supports = sorted(supports, key=lambda x: x["distance"])
        
        # 判断当前位置
        high_20 = recent_highs.max()
        low_20 = recent_lows.min()
        position_ratio = (current_price - low_20) / (high_20 - low_20) * 100 if high_20 > low_20 else 50
        
        if position_ratio > 80:
            position_desc = "高位"
        elif position_ratio > 60:
            position_desc = "中高位"
        elif position_ratio > 40:
            position_desc = "中位"
        elif position_ratio > 20:
            position_desc = "中低位"
        else:
            position_desc = "低位"
        
        return {
            "supports": supports,
            "current_position": position_desc,
            "position_ratio": position_ratio,
            "current_price": current_price
        }
    
    def analyze_retracement_opportunity(self, code: str, name: str = "") -> Dict[str, Any]:
        """
        分析单只股票的回调机会
        
        Args:
            code: 股票代码
            name: 股票名称
            
        Returns:
            回调分析结果
        """
        if not self.data_fetcher:
            return {"error": "数据获取器未初始化"}
        
        try:
            # 获取日线数据
            daily_df = self.data_fetcher.get_daily_data(code, days=30)
            
            if daily_df is None or daily_df.empty:
                return {"error": "无法获取数据"}
            
            # 连续涨跌分析
            consecutive_analysis = self.calculate_consecutive_days(daily_df)
            
            # 支撑位分析
            support_analysis = self.find_support_levels(daily_df)
            
            # 当前基本信息
            latest = daily_df.iloc[-1]
            current_price = float(latest.get("收盘", 0))
            current_change = float(latest.get("涨跌幅", 0))
            
            # 综合建议
            recommendation = self._generate_recommendation(consecutive_analysis, support_analysis, current_change)
            
            return {
                "代码": code,
                "名称": name,
                "当前价格": current_price,
                "今日涨跌幅": current_change,
                "连续分析": consecutive_analysis,
                "支撑分析": support_analysis,
                "操作建议": recommendation,
                "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            return {"error": f"分析失败: {str(e)}"}
    
    def _generate_recommendation(self, consecutive: Dict, support: Dict, current_change: float) -> Dict[str, Any]:
        """
        生成操作建议
        
        Args:
            consecutive: 连续涨跌分析
            support: 支撑分析
            current_change: 当日涨跌幅
            
        Returns:
            操作建议
        """
        risk_level = consecutive["risk_level"]
        rise_days = consecutive["current_consecutive_rise"]
        position = support["position_ratio"]
        
        # 基于连涨天数的建议
        if rise_days >= 5:
            action = "避免介入"
            reason = "连涨5天以上，回调风险极大"
            timing = "等待明显回调后再考虑"
        elif rise_days >= 3:
            action = "谨慎观望"
            reason = "连涨3天以上，需要回调消化"
            timing = "等待回调至重要支撑位"
        elif rise_days >= 2:
            action = "可适量关注"
            reason = "连涨2天，可能面临短期调整"
            timing = "如回调可小仓位试探"
        elif consecutive["current_consecutive_fall"] >= 2:
            action = "积极关注"
            reason = "连续下跌，可能出现反弹"
            timing = "可在支撑位附近介入"
        else:
            action = "正常评估"
            reason = "无明显连续趋势"
            timing = "按常规尾盘策略操作"
        
        # 结合位置调整建议
        if position > 80:
            if action in ["可适量关注", "积极关注"]:
                action = "谨慎观望"
                reason += "，且当前位置偏高"
        elif position < 30:
            if action in ["谨慎观望", "避免介入"]:
                action = "可适量关注"
                reason += "，但当前位置较低"
        
        # 最佳介入点位
        supports = support["supports"]
        best_entry_points = []
        
        for sup in supports[:3]:  # 取前3个最近的支撑位
            if sup["distance"] > 2:  # 距离当前价格2%以上
                best_entry_points.append({
                    "位置": sup["type"],
                    "价格": round(sup["price"], 2),
                    "距离": f"{sup['distance']:.1f}%"
                })
        
        return {
            "操作建议": action,
            "建议原因": reason,
            "介入时机": timing,
            "风险等级": risk_level,
            "最佳介入点": best_entry_points[:2] if best_entry_points else ["当前价格附近"]
        }

def analyze_multiple_stocks(codes: List[str]) -> pd.DataFrame:
    """
    批量分析多只股票
    
    Args:
        codes: 股票代码列表
        
    Returns:
        分析结果DataFrame
    """
    analyzer = ConsecutiveRiseAnalyzer()
    results = []
    
    print(f"📊 开始分析 {len(codes)} 只股票的连涨风险...")
    
    for i, code in enumerate(codes, 1):
        print(f"🔍 进度: {i}/{len(codes)} - 分析 {code}")
        
        analysis = analyzer.analyze_retracement_opportunity(code)
        
        if "error" not in analysis:
            results.append({
                "代码": analysis["代码"],
                "名称": analysis["名称"],
                "当前价格": analysis["当前价格"],
                "今日涨跌幅": f"{analysis['今日涨跌幅']:.2f}%",
                "连涨天数": analysis["连续分析"]["current_consecutive_rise"],
                "风险等级": analysis["连续分析"]["risk_level"],
                "位置": analysis["支撑分析"]["current_position"],
                "操作建议": analysis["操作建议"]["操作建议"],
                "介入时机": analysis["操作建议"]["介入时机"]
            })
    
    if results:
        df = pd.DataFrame(results)
        return df.sort_values("连涨天数", ascending=False)
    else:
        return pd.DataFrame()

def main():
    """主函数"""
    print("🎯 连涨风险分析系统")
    print("=" * 50)
    
    # 示例分析
    analyzer = ConsecutiveRiseAnalyzer()
    
    # 模拟一些连涨股票代码（实际使用时替换为真实选股结果）
    sample_codes = ["000001", "000002", "300001", "600001", "002001"]
    
    print("\n📋 分析模式:")
    print("1. 单股详细分析")
    print("2. 批量风险筛查") 
    
    try:
        choice = input("\n请选择模式 (1/2): ").strip()
        
        if choice == "1":
            code = input("请输入股票代码: ").strip()
            if code:
                print(f"\n🔍 正在分析 {code}...")
                result = analyzer.analyze_retracement_opportunity(code)
                
                if "error" in result:
                    print(f"❌ {result['error']}")
                else:
                    print_detailed_analysis(result)
                    
        elif choice == "2":
            print("\n📊 批量分析示例股票...")
            df = analyze_multiple_stocks(sample_codes)
            
            if not df.empty:
                print("\n📈 连涨风险排行榜:")
                print(df.to_string(index=False))
                
                # 高风险股票提醒
                high_risk = df[df["连涨天数"] >= 3]
                if not high_risk.empty:
                    print(f"\n⚠️ 高风险提醒: {len(high_risk)} 只股票连涨3天以上")
                    print(high_risk[["代码", "名称", "连涨天数", "风险等级"]].to_string(index=False))
            else:
                print("❌ 未获取到有效数据")
        
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")

def print_detailed_analysis(result: Dict[str, Any]):
    """打印详细分析结果"""
    print(f"\n📊 {result['代码']} {result['名称']} - 详细分析")
    print("-" * 40)
    
    print(f"💰 当前价格: {result['当前价格']:.2f}元")
    print(f"📈 今日涨跌: {result['今日涨跌幅']:.2f}%")
    
    # 连续分析
    consecutive = result["连续分析"]
    print(f"\n🔥 连涨分析:")
    print(f"  当前连涨: {consecutive['current_consecutive_rise']}天")
    print(f"  风险等级: {consecutive['risk_level']}")
    print(f"  近5日涨跌: {consecutive['recent_changes']}")
    
    # 支撑分析
    support = result["支撑分析"]
    print(f"\n🛡️ 支撑分析:")
    print(f"  当前位置: {support['current_position']} ({support['position_ratio']:.1f}%)")
    print(f"  重要支撑:")
    
    for sup in support["supports"][:3]:
        print(f"    {sup['type']}: {sup['price']:.2f}元 (距离 {sup['distance']:.1f}%)")
    
    # 操作建议
    recommendation = result["操作建议"]
    print(f"\n💡 操作建议:")
    print(f"  建议行动: {recommendation['操作建议']}")
    print(f"  建议原因: {recommendation['建议原因']}")
    print(f"  介入时机: {recommendation['介入时机']}")
    
    if recommendation["最佳介入点"]:
        print(f"  最佳介入点:")
        for point in recommendation["最佳介入点"]:
            if isinstance(point, dict):
                print(f"    {point['位置']}: {point['价格']}元 (回调{point['距离']})")
            else:
                print(f"    {point}")

if __name__ == "__main__":
    main()
