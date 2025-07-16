import os
import pandas as pd
from datetime import datetime
from data.est.req import est_daily
from data.est.req import est_prepare_data

"""
A股尾盘买入次日卖出策略使用指南

【策略原理】
1. 筛选当日涨幅1-6%的股票，避免追高
2. 要求量比适中（1.1-3.0倍），避免过度炒作
3. 技术形态要求下影线支撑，上影线不过长
4. 短期均线向上，确保趋势良好
5. 近期无大幅异动，价格在合理区间

【最佳买入时机】
📅 周内时机：
- 周一、周二、周三：最佳操作日（流动性好，确定性高）
- 周四：较好（但需关注周五风险）
- 周五：谨慎操作（周末风险，建议避免）

🕐 日内时机：
- 14:30-14:50：黄金时段（推荐）
- 14:50-15:00：最后确认（备选）
- 避免：9:30-11:30（早盘波动大）
- 避免：13:00-14:00（午后开盘不稳定）

【操作建议】
1. 尾盘14:30-15:00之间买入（避免太早买入被套）
2. 次日开盘或上午择机卖出（T+1操作）
3. 设置止损：如次日低开超过-3%，开盘即止损
4. 目标收益：2-5%，不贪心

【风险控制】
1. 单只股票仓位不超过10%
2. 总仓位不超过30%
3. 连续亏损3次暂停操作
4. 遇到大盘系统性风险立即止损

【适用时机】
- 大盘相对稳定或小幅上涨
- 避免在大盘大跌或恐慌时操作
- 重大消息面前谨慎操作
"""


class UpUpPolicy:
    """
    尾盘买入次日卖出策略
    选择适合尾盘买入、次日补涨卖出的股票，基于以下条件：
    1. 当日涨跌幅在 2% 到 7% 之间（有上涨但不过热）
    2. 成交量适中放大（避免过度炒作）
    3. 技术形态良好（下影线较长，上影线较短）
    4. 近期趋势向好（短期均线上涨）
    5. 没有连续大涨（避免追高风险）
    6. 股价在合理区间（避免高位接盘）
    """
    
    def __init__(self, daily_fetcher=None):
        """
        支持传入 EastmoneyDailyStockFetcher 实例，便于依赖注入
        """
        self.daily_fetcher = daily_fetcher or est_daily.EastmoneyDailyStockFetcher()
    
    def select(self) -> pd.DataFrame:
        """
        选择适合尾盘买入、次日补涨卖出的股票
        :return: 满足条件的股票 DataFrame
        """
        members_df = est_prepare_data.load_members_df_from_path()
        if members_df is None or "代码" not in members_df.columns:
            return pd.DataFrame()
        
        result = []
        
        for code in members_df["代码"]:
            try:
                daily_df = self.daily_fetcher.get_daily_df(code)
                if daily_df is None or daily_df.empty or len(daily_df) < 20:
                    continue
                
                # 取最近20天数据
                recent_df = daily_df.tail(20).reset_index(drop=True)
                
                # 获取最新一天的数据
                last_daily = recent_df.iloc[-1]
                
                # 解析涨跌幅
                try:
                    pct_chg = float(last_daily.get("涨跌幅", 0))
                except Exception:
                    pct_chg = 0
                
                # 条件1：当日涨跌幅在1%到6%之间（有上涨但不过热）
                if not (1.0 <= pct_chg <= 6.0):
                    continue
                
                # 解析价格数据
                close_prices = pd.to_numeric(recent_df["收盘"], errors="coerce")
                high_prices = pd.to_numeric(recent_df["最高"], errors="coerce")
                low_prices = pd.to_numeric(recent_df["最低"], errors="coerce")
                open_prices = pd.to_numeric(recent_df["开盘"], errors="coerce")
                
                if (close_prices.isnull().any() or high_prices.isnull().any() or 
                    low_prices.isnull().any() or open_prices.isnull().any()):
                    continue
                
                # 解析成交量数据
                vol = pd.to_numeric(recent_df["成交量"], errors="coerce")
                if vol.isnull().any():
                    continue
                
                today_vol = vol.iloc[-1]
                avg_vol_10 = vol.iloc[-10:].mean()
                
                # 条件2：成交量适中放大（1.1-3.0倍，避免过度炒作）
                volume_ratio = today_vol / avg_vol_10 if avg_vol_10 > 0 else 0
                if not (1.1 <= volume_ratio <= 3.0):
                    continue
                
                # 当日价格数据
                today_high = high_prices.iloc[-1]
                today_low = low_prices.iloc[-1]
                today_open = open_prices.iloc[-1]
                today_close = close_prices.iloc[-1]
                
                # 条件3：技术形态良好（下影线较长或平衡，上影线不太长）
                upper_shadow = today_high - max(today_open, today_close)
                lower_shadow = min(today_open, today_close) - today_low
                body_length = abs(today_close - today_open)
                
                # 如果实体很小，接受更灵活的条件
                if body_length <= 0.5:
                    # 对于十字星等小实体，主要看上影线不太长
                    if upper_shadow > 2.0:  # 上影线不超过2元
                        continue
                else:
                    # 下影线要不小于上影线（表示下方有支撑）
                    if lower_shadow < upper_shadow * 0.8:
                        continue
                    
                    # 上影线不能太长（不超过实体的50%）
                    if upper_shadow > body_length * 0.5:
                        continue
                
                # 条件4：短期均线上涨（3日均线向上即可）
                if len(close_prices) >= 3:
                    avg_3_today = close_prices.iloc[-3:].mean()
                    avg_3_2days_ago = close_prices.iloc[-5:-2].mean() if len(close_prices) >= 5 else close_prices.iloc[-3:].mean()
                    
                    if avg_3_today <= avg_3_2days_ago:
                        continue
                
                # 条件5：没有连续大涨（避免追高风险）
                # 检查过去3天是否有涨幅超过6%的情况
                recent_3_pct = []
                for i in range(max(0, len(recent_df) - 4), len(recent_df) - 1):  # 不包括今天
                    try:
                        day_pct = float(recent_df.iloc[i].get("涨跌幅", 0))
                        recent_3_pct.append(day_pct)
                    except:
                        recent_3_pct.append(0)
                
                if any(p > 6.0 for p in recent_3_pct):
                    continue
                
                # 条件6：股价在合理区间（不在20日内过高位置）
                high_20 = high_prices.iloc[-20:].max()
                low_20 = low_prices.iloc[-20:].min()
                price_position = (today_close - low_20) / (high_20 - low_20) if high_20 > low_20 else 0
                
                # 当前价格不应该在20日内的高位区间（不超过85%）
                if price_position > 0.85:
                    continue
                
                # 计算次日补涨概率评分（0-100分）
                prob_score = 0
                
                # 1. 涨跌幅评分（2-4%为最佳区间）
                if 2.0 <= pct_chg <= 4.0:
                    prob_score += 25
                elif 1.0 <= pct_chg < 2.0:
                    prob_score += 20
                elif 4.0 < pct_chg <= 6.0:
                    prob_score += 15
                
                # 2. 量比评分（1.5-2.5倍为最佳）
                if 1.5 <= volume_ratio <= 2.5:
                    prob_score += 25
                elif 1.2 <= volume_ratio < 1.5:
                    prob_score += 20
                elif 2.5 < volume_ratio <= 3.0:
                    prob_score += 15
                else:
                    prob_score += 10
                
                # 3. 技术形态评分（下影线相对长度）
                if body_length > 0:
                    shadow_ratio = lower_shadow / body_length
                    if shadow_ratio >= 0.8:
                        prob_score += 25
                    elif shadow_ratio >= 0.5:
                        prob_score += 20
                    elif shadow_ratio >= 0.2:
                        prob_score += 15
                    else:
                        prob_score += 10
                else:
                    # 十字星等小实体情况
                    if lower_shadow >= upper_shadow:
                        prob_score += 20
                    else:
                        prob_score += 15
                
                # 4. 位置评分（在20日区间的中低位更好）
                if price_position <= 0.4:
                    prob_score += 20
                elif price_position <= 0.6:
                    prob_score += 15
                elif price_position <= 0.8:
                    prob_score += 10
                else:
                    prob_score += 5
                
                # 5. 趋势评分（3日均线斜率）
                if len(close_prices) >= 6:
                    ma3_today = close_prices.iloc[-3:].mean()
                    ma3_3days_ago = close_prices.iloc[-6:-3].mean()
                    ma3_slope = (ma3_today - ma3_3days_ago) / ma3_3days_ago * 100
                    if ma3_slope > 1:
                        prob_score += 5
                    elif ma3_slope > 0:
                        prob_score += 3
                
                # 满足所有条件的股票
                result.append({
                    "代码": code,
                    "名称": last_daily.get("名称", ""),
                    "涨跌幅": pct_chg,
                    "量比": volume_ratio,
                    "收盘价": today_close,
                    "上影线": upper_shadow,
                    "下影线": lower_shadow,
                    "实体长度": body_length,
                    "影线比": lower_shadow / body_length if body_length > 0 else 0,
                    "20日位置": price_position * 100,
                    "次日补涨概率": prob_score
                })
                
            except Exception as e:
                print(f"{code} 处理异常: {e}")
                continue
        
        if not result:
            return pd.DataFrame()
        
        # 按次日补涨概率降序排列
        df = pd.DataFrame(result)
        return df.sort_values(by="次日补涨概率", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    policy = UpUpPolicy()
    up_stocks = policy.select()
    
    # 时间判断
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    # 判断当前时机
    def get_timing_advice():
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
        if current_time >= datetime.strptime("14:30", "%H:%M").time() and current_time <= datetime.strptime("15:00", "%H:%M").time():
            if current_time <= datetime.strptime("14:50", "%H:%M").time():
                advice.append("🟢 当前为黄金买入时段（14:30-14:50）")
            else:
                advice.append("🟡 当前为最后确认时段（14:50-15:00）")
        elif current_time < datetime.strptime("14:30", "%H:%M").time() and current_time > datetime.strptime("09:30", "%H:%M").time():
            advice.append("⏰ 建议等待14:30后再考虑买入")
        elif current_time > datetime.strptime("15:00", "%H:%M").time():
            advice.append("⏰ 今日交易已结束，可为明日做准备")
        else:
            advice.append("⏰ 市场未开盘")
        
        return advice
    
    timing_advice = get_timing_advice()
    
    print("=== 尾盘买入次日补涨股票 ===")
    print(f"分析时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 显示时机建议
    print("【时机分析】")
    for advice in timing_advice:
        print(f"  {advice}")
    print()
    
    if up_stocks.empty:
        print("当前没有符合条件的尾盘买入股票")
    else:
        print(f"找到 {len(up_stocks)} 只适合尾盘买入的股票：")
        print()
        
        for i, row in up_stocks.iterrows():
            print(f"【排名 {i+1}】{row['名称']}（{row['代码']}）")
            print(f"  涨跌幅: {row['涨跌幅']:.2f}%")
            print(f"  次日补涨概率: {row['次日补涨概率']:.0f}分")
            print(f"  量比: {row['量比']:.2f}倍")
            print(f"  收盘价: {row['收盘价']:.2f}元")
            print(f"  20日位置: {row['20日位置']:.1f}%")
            print(f"  影线比: {row['影线比']:.2f}（下/实体）")
            print(f"  技术形态: 上影线{row['上影线']:.2f} 下影线{row['下影线']:.2f} 实体{row['实体长度']:.2f}")
            
            # 添加操作建议
            if row['次日补涨概率'] >= 75:
                print(f"  🟢 操作建议: 强烈推荐尾盘买入")
            elif row['次日补涨概率'] >= 65:
                print(f"  🟡 操作建议: 适合尾盘买入")
            else:
                print(f"  🟠 操作建议: 谨慎考虑")
            
            # 添加风险提示
            if row['20日位置'] > 80:
                print(f"  ⚠️  风险提示: 位置较高，注意风险")
            elif row['量比'] > 2.5:
                print(f"  ⚠️  风险提示: 量比较高，注意追高风险")
            
            print()
        
        # 保存详细信息
        output_path = "/Users/kevin/Downloads/up_up_data.txt"
        codes = ",".join(map(str, up_stocks["代码"]))
        
        # 保存详细报告
        report_path = "/Users/kevin/Downloads/up_up_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=== 尾盘买入次日补涨股票分析报告 ===\n\n")
            f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"符合条件股票数量: {len(up_stocks)}\n\n")
            
            # 写入时机分析
            f.write("【时机分析】\n")
            for advice in timing_advice:
                f.write(f"  {advice}\n")
            f.write("\n")
            
            f.write("策略说明:\n")
            f.write("1. 适合尾盘买入，次日上午或中午卖出\n")
            f.write("2. 选择涨幅1-6%的股票，避免追高\n")
            f.write("3. 重点关注下影线长的股票（有支撑）\n")
            f.write("4. 量比适中（1.1-3.0倍），避免过度炒作\n")
            f.write("5. 价格不在20日高位，降低风险\n\n")
            
            f.write("【最佳买入时机】\n")
            f.write("周内: 周一至周三最佳，周四可行，周五谨慎\n")
            f.write("日内: 14:30-14:50黄金时段，14:50-15:00最后确认\n\n")
            
            for i, row in up_stocks.iterrows():
                f.write(f"【排名 {i+1}】{row['名称']}（{row['代码']}）\n")
                f.write(f"  涨跌幅: {row['涨跌幅']:.2f}%\n")
                f.write(f"  次日补涨概率: {row['次日补涨概率']:.0f}分\n")
                f.write(f"  量比: {row['量比']:.2f}倍\n")
                f.write(f"  收盘价: {row['收盘价']:.2f}元\n")
                f.write(f"  20日位置: {row['20日位置']:.1f}%\n")
                f.write(f"  影线比: {row['影线比']:.2f}（下影线/实体）\n")
                f.write(f"  技术形态: 上影线{row['上影线']:.2f} 下影线{row['下影线']:.2f} 实体{row['实体长度']:.2f}\n")
                f.write("\n")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(codes)
            mtime = os.path.getmtime(output_path)
            print(f"股票代码保存到: {output_path}")
            print(f"详细报告保存到: {report_path}")
            print(f"最后修改时间: {datetime.fromtimestamp(mtime)}")
        except Exception as e:
            print(f"保存文件时出错: {e}")