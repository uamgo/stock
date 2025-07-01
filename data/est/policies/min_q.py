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

        stage1_codes = []
        stage2_codes = []
        stage3_codes = []
        result = []

        for code in members_df["代码"]:
            try:
                daily_df = self.daily_fetcher.get_daily_df(code)
                if daily_df is None or daily_df.empty or len(daily_df) < 7:
                    continue

                # 1. 最近5天内有过爆量（最高量是第二高的两倍以上）
                recent5_df = daily_df.tail(5).reset_index(drop=True)
                vol5 = pd.to_numeric(recent5_df["成交量"], errors="coerce")
                if vol5.isnull().any():
                    continue
                vol5_sorted = vol5.sort_values(ascending=False).values
                if len(vol5_sorted) < 2 or vol5_sorted[0] < 2 * vol5_sorted[1]:
                    continue
                stage1_codes.append(code)
                # 阶段1结束

                # 2. 最近一个交易日的量是最高量的两倍以下，且最后一个交易日的最低点高于前一日的最低点
                last_vol = vol5.iloc[-1]
                max_vol = vol5.max()
                if last_vol > 2 * max_vol:
                    continue
                last_low = pd.to_numeric(recent5_df["最低"], errors="coerce").iloc[-1]
                prev_low = pd.to_numeric(recent5_df["最低"], errors="coerce").iloc[-2]
                if last_low <= prev_low:
                    continue
                stage2_codes.append(code)
                # 阶段2结束

                # 3. 如果今天是交易日，且按照已过去的交易时间占比*7日最高量*50% > 最后一个交易日的成交量，则选出来
                recent7_df = daily_df.tail(7).reset_index(drop=True)
                vol7 = pd.to_numeric(recent7_df["成交量"], errors="coerce")
                if vol7.isnull().any():
                    continue
                ratio = get_trading_time_ratio() if est_common.is_in_trading_time() else 1
                threshold = vol7.max() * ratio * 0.5
                if threshold > last_vol:
                    result.append({
                        "代码": code,
                        "名称": recent5_df.iloc[-1].get("名称", ""),
                        "今日成交量": last_vol,
                        "5日最大量": max_vol,
                        "7日最大量": vol7.max(),
                        "最低": last_low,
                        "前一日最低": prev_low,
                        "时间占比阈值": threshold
                    })
                    stage3_codes.append(code)
            except Exception as e:
                print(f"{code} 处理异常: {e}")

        print(f"阶段1通过股票数量: {len(stage1_codes)}")
        print(f"阶段2通过股票数量: {len(stage2_codes)}")
        print(f"阶段3通过股票数量: {len(stage3_codes)}")

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
            print(f"保存的文件名: {output_path}")
        except Exception as e:
            print(f"保存文件时出错: {e}")
