import os
from datetime import datetime, time
import pandas as pd
from data.est.req import est_daily
from data.est.req import est_common
from data.est.req import est_prepare_data

def is_before_open():
    # 假设9:30开盘
    return datetime.now().time() < time(9, 30)

def get_trading_time_ratio():
    # 假设A股 9:30-11:30, 13:00-15:00，共4小时
    now = datetime.now().time()
    if now < time(9, 30):
        return 0
    elif now <= time(11, 30):
        minutes = (now.hour - 9) * 60 + (now.minute - 30)
        return max(0, min(minutes / 240, 1))
    elif now < time(13, 0):
        return 0.5
    elif now <= time(15, 0):
        minutes = 120 + (now.hour - 13) * 60 + now.minute
        return max(0, min(minutes / 240, 1))
    else:
        return 1

class MinQPolicy:
    """
    股票缩量与爆量策略（无黑名单逻辑）
    """
    def __init__(self, daily_fetcher=None):
        self.daily_fetcher = daily_fetcher or est_daily.EastmoneyDailyStockFetcher()

    def select(self, members_df: pd.DataFrame) -> pd.DataFrame:
        if members_df is None or "代码" not in members_df.columns:
            return pd.DataFrame()

        result = []

        for code in members_df["代码"]:
            try:
                daily_df = self.daily_fetcher.get_daily_df(code)
                if daily_df is None or daily_df.empty or len(daily_df) < 7:
                    continue
                # 计算20日均价，仅当数据量足够时
                if len(daily_df) > 20:
                    last20_close = pd.to_numeric(daily_df.tail(20)["收盘"], errors="coerce")
                    if last20_close.isnull().any():
                        continue
                    avg_20 = last20_close.mean()
                    # 获取最后一日收盘价
                    last_close = pd.to_numeric(daily_df.tail(1)["收盘"], errors="coerce").iloc[0]
                    # 淘汰最后一日收盘价在均价以下的股票
                    if last_close < avg_20:
                        continue
                    # 淘汰当前价格超出20日均价线10%以上的股票
                    if last_close > avg_20 * 1.05:
                        continue
                # 只判断最后一个交易日和前一个交易日是否缩量下跌
                recent2_df = daily_df.tail(2).reset_index(drop=True)
                vol = pd.to_numeric(recent2_df["成交量"], errors="coerce")
                close = pd.to_numeric(recent2_df["收盘"], errors="coerce")
                if vol.isnull().any() or close.isnull().any():
                    continue

                last_vol = vol.iloc[-1]
                prev_vol = vol.iloc[-2]
                last_close = close.iloc[-1]
                prev_close = close.iloc[-2]

                # 近7日最高量和最低量
                last7_vol = pd.to_numeric(daily_df.tail(7)["成交量"], errors="coerce")
                if last7_vol.isnull().any():
                    continue
                max_vol_7 = last7_vol.max()
                min_vol_7 = last7_vol.min()
                if min_vol_7 == 0 or max_vol_7 < 2 * min_vol_7:
                    continue

                # 排除今日最低价格比昨天最低价低的股票
                low = pd.to_numeric(recent2_df["最低"], errors="coerce")
                if low.isnull().any():
                    continue
                last_low = low.iloc[-1]
                prev_low = low.iloc[-2]
                if last_low < prev_low:
                    continue

                # 今日跌幅
                if prev_close == 0:
                    continue
                pct_chg = (last_close - prev_close) / prev_close * 100

                if last_vol < prev_vol and last_close < prev_close and pct_chg > -3:
                    result.append({
                    "代码": code,
                    "名称": recent2_df.iloc[-1].get("名称", ""),
                    "今日成交量": last_vol,
                    "昨日成交量": prev_vol,
                    "今日收盘": last_close,
                    "昨日收盘": prev_close,
                    "今日跌幅%": pct_chg,
                    "7日最高量": max_vol_7,
                    "7日最低量": min_vol_7
                    })
            except Exception as e:
                print(f"{code} 处理异常: {e}")

        if not result:
            return pd.DataFrame()
        return pd.DataFrame(result).sort_values(by="今日成交量", ascending=True).reset_index(drop=True)

if __name__ == "__main__":
    members_df = est_prepare_data.load_members_df_from_path()
    policy = MinQPolicy()
    minq_df = policy.select(members_df)
    print(minq_df)
    if not minq_df.empty:
        output_path = "/Users/kevin/Downloads/min_q_data.txt"
        codes = ",".join(map(str, minq_df["代码"]))
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(codes)
            mtime = os.path.getmtime(output_path)
            print(f"保存的文件名: {output_path}, 最后修改时间: {datetime.fromtimestamp(mtime)}")
        except Exception as e:
            print(f"保存文件时出错: {e}")
