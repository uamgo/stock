#!/usr/bin/env python3
"""
放量回调形态分析系统

专门分析放量上涨后回调到支撑位的优质股票形态
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
    from tail_trading.data.eastmoney.daily_fetcher import EastmoneyDataFetcher
except ImportError:
    print("⚠️ 无法导入数据模块，使用模拟数据")

class VolumeRetracementAnalyzer:
    """放量回调分析器"""
    
    def __init__(self):
        try:
            self.data_fetcher = EastmoneyDataFetcher()
        except:
            self.data_fetcher = None
    
    def analyze_volume_pattern(self, daily_df: pd.DataFrame, days: int = 10) -> Dict[str, Any]:
        """
        分析成交量形态
        
        Args:
            daily_df: 日线数据
            days: 分析天数
            
        Returns:
            成交量分析结果
        """
        if daily_df.empty or len(daily_df) < days:
            return {"error": "数据不足"}
        
        # 获取成交量和价格数据
        volumes = pd.to_numeric(daily_df["成交量"], errors="coerce").fillna(0)
        closes = pd.to_numeric(daily_df["收盘"], errors="coerce").fillna(0)
        pct_changes = pd.to_numeric(daily_df["涨跌幅"], errors="coerce").fillna(0)
        
        recent_data = daily_df.tail(days)
        recent_volumes = volumes.tail(days)
        recent_closes = closes.tail(days)
        recent_changes = pct_changes.tail(days)
        
        # 计算均量
        avg_volume_5 = recent_volumes.tail(5).mean()
        avg_volume_10 = recent_volumes.tail(10).mean() if len(recent_volumes) >= 10 else avg_volume_5
        avg_volume_20 = volumes.tail(20).mean() if len(volumes) >= 20 else avg_volume_10
        
        # 寻找放量上涨日
        volume_surge_days = []
        for i in range(len(recent_data)):
            vol = recent_volumes.iloc[i]
            change = recent_changes.iloc[i]
            
            # 放量标准：成交量大于5日均量1.5倍且上涨
            if vol > avg_volume_5 * 1.5 and change > 2:
                volume_surge_days.append({
                    "日期": recent_data.iloc[i]["日期"],
                    "涨跌幅": change,
                    "成交量": vol,
                    "量比": vol / avg_volume_5,
                    "价格": recent_closes.iloc[i]
                })
        
        # 分析放量后的回调
        retracement_analysis = self._analyze_post_volume_retracement(
            recent_data, recent_volumes, recent_closes, recent_changes, avg_volume_5
        )
        
        # 当前成交量状态
        current_volume = recent_volumes.iloc[-1]
        current_change = recent_changes.iloc[-1]
        
        volume_status = self._classify_volume_status(current_volume, avg_volume_5, avg_volume_10)
        
        return {
            "放量上涨日": volume_surge_days,
            "回调分析": retracement_analysis,
            "当前成交量": current_volume,
            "5日均量": avg_volume_5,
            "10日均量": avg_volume_10,
            "20日均量": avg_volume_20,
            "成交量状态": volume_status,
            "量价配合度": self._calculate_volume_price_correlation(recent_volumes, recent_changes)
        }
    
    def _analyze_post_volume_retracement(self, data_df, volumes, closes, changes, avg_vol) -> Dict[str, Any]:
        """分析放量后的回调情况"""
        
        # 找到最近的放量上涨日
        last_surge_idx = -1
        for i in range(len(data_df) - 1, -1, -1):
            if volumes.iloc[i] > avg_vol * 1.5 and changes.iloc[i] > 2:
                last_surge_idx = i
                break
        
        if last_surge_idx == -1:
            return {"状态": "未发现近期放量", "评分": 0}
        
        surge_price = closes.iloc[last_surge_idx]
        current_price = closes.iloc[-1]
        
        # 计算从放量日到现在的回调幅度
        retracement_pct = (current_price - surge_price) / surge_price * 100
        
        # 分析回调期间的成交量
        post_surge_volumes = volumes.iloc[last_surge_idx+1:]
        volume_shrink = post_surge_volumes.mean() / volumes.iloc[last_surge_idx] if len(post_surge_volumes) > 0 else 1
        
        # 评估回调质量
        quality_score = 0
        
        # 回调幅度评分（2-8%为理想回调）
        if -8 <= retracement_pct <= -2:
            quality_score += 30
        elif -12 <= retracement_pct < -8:
            quality_score += 20
        elif 0 <= retracement_pct <= 2:
            quality_score += 10
        else:
            quality_score -= 10
        
        # 缩量回调加分
        if volume_shrink < 0.7:
            quality_score += 25
        elif volume_shrink < 0.8:
            quality_score += 15
        
        # 时间因子（放量后1-5天回调最佳）
        days_since_surge = len(data_df) - 1 - last_surge_idx
        if 1 <= days_since_surge <= 5:
            quality_score += 20
        elif days_since_surge > 7:
            quality_score -= 15
        
        return {
            "状态": "发现放量回调",
            "放量日期": data_df.iloc[last_surge_idx]["日期"],
            "放量涨幅": changes.iloc[last_surge_idx],
            "回调幅度": retracement_pct,
            "回调天数": days_since_surge,
            "缩量比例": volume_shrink,
            "质量评分": max(0, min(100, quality_score))
        }
    
    def _classify_volume_status(self, current_vol: float, avg_5: float, avg_10: float) -> str:
        """分类成交量状态"""
        if current_vol > avg_5 * 2:
            return "巨量"
        elif current_vol > avg_5 * 1.5:
            return "放量"
        elif current_vol > avg_5 * 1.2:
            return "温和放量"
        elif current_vol < avg_5 * 0.7:
            return "缩量"
        elif current_vol < avg_5 * 0.5:
            return "极度缩量"
        else:
            return "正常量"
    
    def _calculate_volume_price_correlation(self, volumes: pd.Series, changes: pd.Series) -> float:
        """计算量价配合度"""
        try:
            # 计算成交量和涨跌幅的相关系数
            correlation = np.corrcoef(volumes, changes)[0, 1]
            return round(correlation, 3) if not np.isnan(correlation) else 0
        except:
            return 0
    
    def analyze_stock_pattern(self, daily_df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析股票技术形态
        
        Args:
            daily_df: 日线数据
            
        Returns:
            形态分析结果
        """
        if daily_df.empty or len(daily_df) < 20:
            return {"error": "数据不足"}
        
        closes = pd.to_numeric(daily_df["收盘"], errors="coerce").fillna(0)
        highs = pd.to_numeric(daily_df["最高"], errors="coerce").fillna(0)
        lows = pd.to_numeric(daily_df["最低"], errors="coerce").fillna(0)
        
        # 均线形态
        ma5 = closes.rolling(5).mean()
        ma10 = closes.rolling(10).mean()
        ma20 = closes.rolling(20).mean()
        
        current_price = closes.iloc[-1]
        current_ma5 = ma5.iloc[-1]
        current_ma10 = ma10.iloc[-1]
        current_ma20 = ma20.iloc[-1]
        
        # 均线排列
        ma_alignment = self._analyze_ma_alignment(current_price, current_ma5, current_ma10, current_ma20)
        
        # 趋势强度
        trend_strength = self._calculate_trend_strength(closes, ma20)
        
        # 支撑阻力
        support_resistance = self._find_support_resistance(highs, lows, closes)
        
        # 形态评分
        pattern_score = self._calculate_pattern_score(ma_alignment, trend_strength, support_resistance, closes)
        
        return {
            "均线排列": ma_alignment,
            "趋势强度": trend_strength,
            "支撑阻力": support_resistance,
            "当前价格": current_price,
            "MA5": round(current_ma5, 2),
            "MA10": round(current_ma10, 2),
            "MA20": round(current_ma20, 2),
            "形态评分": pattern_score
        }
    
    def _analyze_ma_alignment(self, price: float, ma5: float, ma10: float, ma20: float) -> Dict[str, Any]:
        """分析均线排列"""
        
        # 多头排列：价格>MA5>MA10>MA20
        if price > ma5 > ma10 > ma20:
            alignment = "完美多头排列"
            score = 100
        elif price > ma5 > ma10:
            alignment = "多头排列"
            score = 80
        elif price > ma5:
            alignment = "短期多头"
            score = 60
        elif ma5 > ma10 > ma20:
            alignment = "均线多头"
            score = 40
        elif ma5 < ma10 < ma20:
            alignment = "空头排列"
            score = 20
        else:
            alignment = "混乱排列"
            score = 30
        
        return {
            "类型": alignment,
            "评分": score,
            "价格位置": "均线上方" if price > ma5 else "均线下方"
        }
    
    def _calculate_trend_strength(self, closes: pd.Series, ma20: pd.Series) -> Dict[str, Any]:
        """计算趋势强度"""
        
        # 20日均线斜率
        ma20_slope = (ma20.iloc[-1] - ma20.iloc[-5]) / ma20.iloc[-5] * 100 if len(ma20) >= 5 else 0
        
        # 价格相对于MA20的位置
        price_vs_ma20 = (closes.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1] * 100
        
        # 最近5日涨跌幅
        recent_change = (closes.iloc[-1] - closes.iloc[-6]) / closes.iloc[-6] * 100 if len(closes) >= 6 else 0
        
        # 趋势强度评分
        strength_score = 0
        if ma20_slope > 2:
            strength_score += 30
        elif ma20_slope > 0:
            strength_score += 15
        
        if price_vs_ma20 > 5:
            strength_score += 25
        elif price_vs_ma20 > 0:
            strength_score += 15
        
        if recent_change > 10:
            strength_score += 25
        elif recent_change > 0:
            strength_score += 10
        
        # 趋势分类
        if strength_score >= 70:
            trend_type = "强势上涨"
        elif strength_score >= 50:
            trend_type = "温和上涨"
        elif strength_score >= 30:
            trend_type = "震荡上行"
        else:
            trend_type = "趋势不明"
        
        return {
            "类型": trend_type,
            "评分": strength_score,
            "MA20斜率": round(ma20_slope, 2),
            "价格偏离": round(price_vs_ma20, 2),
            "近期涨幅": round(recent_change, 2)
        }
    
    def _find_support_resistance(self, highs: pd.Series, lows: pd.Series, closes: pd.Series) -> Dict[str, Any]:
        """寻找支撑和阻力位"""
        
        current_price = closes.iloc[-1]
        
        # 近期高低点
        recent_high = highs.tail(10).max()
        recent_low = lows.tail(10).min()
        
        # 距离支撑和阻力的百分比
        support_distance = (current_price - recent_low) / current_price * 100
        resistance_distance = (recent_high - current_price) / current_price * 100
        
        # 位置评估
        position_in_range = (current_price - recent_low) / (recent_high - recent_low) * 100 if recent_high > recent_low else 50
        
        return {
            "近期支撑": round(recent_low, 2),
            "近期阻力": round(recent_high, 2),
            "支撑距离": round(support_distance, 2),
            "阻力距离": round(resistance_distance, 2),
            "位置比例": round(position_in_range, 2)
        }
    
    def _calculate_pattern_score(self, ma_alignment: Dict, trend_strength: Dict, 
                               support_resistance: Dict, closes: pd.Series) -> int:
        """计算综合形态评分"""
        
        score = 0
        
        # 均线排列评分
        score += ma_alignment["评分"] * 0.3
        
        # 趋势强度评分
        score += trend_strength["评分"] * 0.4
        
        # 位置评分（中低位加分）
        position = support_resistance["位置比例"]
        if position < 30:
            score += 20
        elif position < 50:
            score += 15
        elif position < 70:
            score += 10
        else:
            score -= 10
        
        # 近期表现评分
        if len(closes) >= 5:
            recent_performance = (closes.iloc[-1] - closes.iloc[-5]) / closes.iloc[-5] * 100
            if 0 < recent_performance < 15:
                score += 15
            elif recent_performance >= 15:
                score += 5
        
        return int(max(0, min(100, score)))
    
    def comprehensive_analysis(self, code: str, name: str = "") -> Dict[str, Any]:
        """
        综合分析：放量回调 + 形态分析（使用真实数据）
        
        Args:
            code: 股票代码
            name: 股票名称
            
        Returns:
            综合分析结果
        """
        if not self.data_fetcher:
            # 备用数据获取方案
            try:
                from data.est.req.est_daily import EastmoneyDailyStockFetcher
                daily_fetcher = EastmoneyDailyStockFetcher()
                daily_df = daily_fetcher.get_daily_df(code)
                
                if daily_df is None or daily_df.empty:
                    return {"error": "无法获取股票数据"}
                
                # 使用备用数据进行分析
                return self._analyze_with_fallback_data(code, name, daily_df)
                
            except ImportError:
                return {"error": "数据获取器和备用模块都未初始化"}
            except Exception as e:
                return {"error": f"备用数据分析失败: {str(e)}"}
        
        try:
            # 获取30天数据
            daily_df = self.data_fetcher.get_daily_data(code, days=30)
            
            if daily_df is None or daily_df.empty:
                # 尝试备用方案
                try:
                    from data.est.req.est_daily import EastmoneyDailyStockFetcher
                    daily_fetcher = EastmoneyDailyStockFetcher()
                    daily_df = daily_fetcher.get_daily_df(code)
                    
                    if daily_df is not None and not daily_df.empty:
                        return self._analyze_with_fallback_data(code, name, daily_df)
                        
                except Exception:
                    pass
                
                return {"error": "无法获取数据"}
            
            # 成交量分析
            volume_analysis = self.analyze_volume_pattern(daily_df)
            
            # 形态分析
            pattern_analysis = self.analyze_stock_pattern(daily_df)
            
            # 综合评分
            final_score = self._calculate_final_score(volume_analysis, pattern_analysis)
            
            # 投资建议
            recommendation = self._generate_investment_advice(volume_analysis, pattern_analysis, final_score)
            
            return {
                "代码": code,
                "名称": name or self._get_stock_name(code),
                "成交量分析": volume_analysis,
                "形态分析": pattern_analysis,
                "综合评分": final_score,
                "投资建议": recommendation,
                "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "数据来源": "主要数据源"
            }
            
        except Exception as e:
            return {"error": f"分析失败: {str(e)}"}
    
    def _analyze_with_fallback_data(self, code: str, name: str, daily_df: pd.DataFrame) -> Dict[str, Any]:
        """使用备用数据进行分析"""
        try:
            # 成交量分析
            volume_analysis = self.analyze_volume_pattern(daily_df)
            
            # 形态分析  
            pattern_analysis = self.analyze_stock_pattern(daily_df)
            
            # 综合评分
            final_score = self._calculate_final_score(volume_analysis, pattern_analysis)
            
            # 投资建议
            recommendation = self._generate_investment_advice(volume_analysis, pattern_analysis, final_score)
            
            return {
                "代码": code,
                "名称": name or self._get_stock_name(code),
                "成交量分析": volume_analysis,
                "形态分析": pattern_analysis,
                "综合评分": final_score,
                "投资建议": recommendation,
                "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "数据来源": "备用数据源"
            }
        except Exception as e:
            return {"error": f"备用分析失败: {str(e)}"}
    
    def _get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        name_map = {
            "000001": "平安银行",
            "000002": "万科A", 
            "000858": "五粮液",
            "002415": "海康威视",
            "300001": "特锐德",
            "300122": "智飞生物",
            "600001": "邮储银行",
            "600036": "招商银行",
            "600519": "贵州茅台"
        }
        return name_map.get(code, f"股票{code}")
    
    def _calculate_final_score(self, volume_analysis: Dict, pattern_analysis: Dict) -> int:
        """计算最终综合评分"""
        
        volume_score = 0
        pattern_score = pattern_analysis.get("形态评分", 0)
        
        # 成交量评分
        if "error" not in volume_analysis:
            retracement = volume_analysis.get("回调分析", {})
            if retracement.get("状态") == "发现放量回调":
                volume_score = retracement.get("质量评分", 0)
            
            # 量价配合度加分
            correlation = volume_analysis.get("量价配合度", 0)
            if correlation > 0.3:
                volume_score += 15
            elif correlation > 0.1:
                volume_score += 8
        
        # 综合评分（量价各占50%）
        final_score = int(volume_score * 0.5 + pattern_score * 0.5)
        
        return max(0, min(100, final_score))
    
    def _generate_investment_advice(self, volume_analysis: Dict, pattern_analysis: Dict, score: int) -> Dict[str, Any]:
        """生成投资建议"""
        
        if score >= 80:
            level = "强烈推荐"
            action = "重点关注，可积极介入"
        elif score >= 70:
            level = "推荐"
            action = "值得关注，可适量介入"
        elif score >= 60:
            level = "一般"
            action = "可以关注，小仓位试探"
        elif score >= 40:
            level = "谨慎"
            action = "谨慎观望，等待更好机会"
        else:
            level = "不推荐"
            action = "暂不考虑"
        
        # 具体建议
        suggestions = []
        
        # 基于成交量分析的建议
        if "error" not in volume_analysis:
            retracement = volume_analysis.get("回调分析", {})
            if retracement.get("状态") == "发现放量回调":
                if retracement.get("质量评分", 0) > 60:
                    suggestions.append("放量回调形态良好，可关注支撑位介入机会")
                else:
                    suggestions.append("放量回调质量一般，需要更多确认信号")
        
        # 基于形态分析的建议
        ma_alignment = pattern_analysis.get("均线排列", {})
        if ma_alignment.get("评分", 0) > 70:
            suggestions.append("均线排列良好，趋势向上")
        
        trend = pattern_analysis.get("趋势强度", {})
        if trend.get("评分", 0) > 60:
            suggestions.append("趋势强度较好，上升动能充足")
        
        return {
            "推荐等级": level,
            "操作建议": action,
            "具体建议": suggestions,
            "风险提示": "注意控制仓位，设置止损位"
        }

def main():
    """主函数"""
    print("📊 放量回调形态分析系统")
    print("=" * 50)
    
    analyzer = VolumeRetracementAnalyzer()
    
    # 示例分析
    sample_codes = ["000001", "000002", "300001", "600001", "002001"]
    
    print("请选择分析模式:")
    print("1. 单股详细分析")
    print("2. 批量筛选分析")
    
    try:
        choice = input("\n请选择 (1/2): ").strip()
        
        if choice == "1":
            code = input("请输入股票代码: ").strip()
            if code:
                print(f"\n🔍 正在分析 {code}...")
                result = analyzer.comprehensive_analysis(code)
                
                if "error" in result:
                    print(f"❌ {result['error']}")
                else:
                    print_detailed_result(result)
        
        elif choice == "2":
            print(f"\n📊 批量分析 {len(sample_codes)} 只股票...")
            results = []
            
            for i, code in enumerate(sample_codes, 1):
                print(f"🔍 进度: {i}/{len(sample_codes)} - 分析 {code}")
                result = analyzer.comprehensive_analysis(code)
                
                if "error" not in result:
                    results.append({
                        "代码": result["代码"],
                        "名称": result["名称"],
                        "综合评分": result["综合评分"],
                        "推荐等级": result["投资建议"]["推荐等级"],
                        "放量回调": "是" if result["成交量分析"].get("回调分析", {}).get("状态") == "发现放量回调" else "否",
                        "形态评分": result["形态分析"].get("形态评分", 0)
                    })
            
            if results:
                df = pd.DataFrame(results)
                df = df.sort_values("综合评分", ascending=False)
                print(f"\n📈 放量回调股票排行榜:")
                print(df.to_string(index=False))
                
                # 高评分股票
                high_score = df[df["综合评分"] >= 70]
                if not high_score.empty:
                    print(f"\n⭐ 高评分推荐 ({len(high_score)} 只):")
                    print(high_score.to_string(index=False))
            else:
                print("❌ 未获取到有效数据")
        
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")

def print_detailed_result(result: Dict[str, Any]):
    """打印详细分析结果"""
    print(f"\n📊 {result['代码']} {result['名称']} - 放量回调形态分析")
    print("=" * 60)
    
    # 综合评分
    score = result["综合评分"]
    print(f"⭐ 综合评分: {score}/100")
    
    # 成交量分析
    volume = result["成交量分析"]
    if "error" not in volume:
        print(f"\n📈 成交量分析:")
        print(f"  当前成交量状态: {volume['成交量状态']}")
        print(f"  量价配合度: {volume['量价配合度']}")
        
        retracement = volume.get("回调分析", {})
        if retracement.get("状态") == "发现放量回调":
            print(f"  🎯 发现放量回调:")
            print(f"    放量日期: {retracement['放量日期']}")
            print(f"    回调幅度: {retracement['回调幅度']:.2f}%")
            print(f"    回调天数: {retracement['回调天数']}天")
            print(f"    质量评分: {retracement['质量评分']}/100")
        else:
            print(f"  ⚠️ {retracement.get('状态', '未分析')}")
    
    # 形态分析
    pattern = result["形态分析"]
    if "error" not in pattern:
        print(f"\n📊 形态分析:")
        print(f"  形态评分: {pattern['形态评分']}/100")
        print(f"  均线排列: {pattern['均线排列']['类型']}")
        print(f"  趋势强度: {pattern['趋势强度']['类型']}")
        print(f"  当前价格: {pattern['当前价格']:.2f}元")
        print(f"  MA5/MA10/MA20: {pattern['MA5']}/{pattern['MA10']}/{pattern['MA20']}")
    
    # 投资建议
    advice = result["投资建议"]
    print(f"\n💡 投资建议:")
    print(f"  推荐等级: {advice['推荐等级']}")
    print(f"  操作建议: {advice['操作建议']}")
    
    if advice["具体建议"]:
        print(f"  具体建议:")
        for suggestion in advice["具体建议"]:
            print(f"    • {suggestion}")
    
    print(f"  风险提示: {advice['风险提示']}")

if __name__ == "__main__":
    main()
