import pandas as pd
from data.est.req import est_daily
from data.est.req import est_prepare_data
import os
from datetime import datetime


class FistUpPolicy:
    """
    近20天首放量股票策略
    """
    def __init__(self, daily_fetcher=None):
        """
        支持传入 EastmoneyDailyStockFetcher 实例，便于依赖注入
        """
        self.daily_fetcher = daily_fetcher or est_daily.EastmoneyDailyStockFetcher()

    def select(self) -> pd.DataFrame:
        """
        找到近20天首次放量且涨幅大于3%的股票
        :param members_df: 包含股票代码的 DataFrame，需有“代码”列
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
                # 只取最近20天
                recent_df = daily_df.tail(20).reset_index(drop=True)
                vol = pd.to_numeric(recent_df["成交量"], errors="coerce")
                if vol.isnull().any():
                    continue
                today_vol = vol.iloc[-1]
                max_vol_20 = vol.max()
                last_daily = recent_df.iloc[-1]
                try:
                    pct_chg = float(last_daily.get("涨跌幅", 0))
                except Exception:
                    pct_chg = 0

                # 计算上影线和下影线
                try:
                    high = float(last_daily.get("最高", 0))
                    low = float(last_daily.get("最低", 0))
                    open_ = float(last_daily.get("开盘", 0))
                    close = float(last_daily.get("收盘", 0))
                    upper_shadow = high - max(open_, close)
                    lower_shadow = min(open_, close) - low
                    if close <= open_:
                        continue
                except Exception:
                    upper_shadow = 0
                    lower_shadow = 0

                # 首放量：今日成交量等于近20日最大且前19天都小于今日
                # 新增条件：上影线小于下影线
                if (
                    today_vol >= max_vol_20
                    and pct_chg > 3
                    and (vol[:-1] < today_vol).all()
                    and upper_shadow < lower_shadow
                ):
                    result.append({
                    "代码": code,
                    "名称": last_daily.get("名称", ""),
                    "涨跌幅": pct_chg,
                    "今日成交量": today_vol,
                    "20日最大量": max_vol_20
                    })
            except Exception as e:
                print(f"{code} 处理异常: {e}")
            continue
        if not result:
            return pd.DataFrame()
        df = pd.DataFrame(result)
        return df.sort_values(by="涨跌幅", ascending=False).reset_index(drop=True)

if __name__ == "__main__":
    policy = FistUpPolicy()
    up_df = policy.select()
    print(up_df)
    if not up_df.empty:
        output_path = "/Users/kevin/Downloads/first_up_data.txt"
        codes = ",".join(map(str, up_df["代码"]))
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(codes)
            mtime = os.path.getmtime(output_path)
            print(f"保存的文件名: {output_path}，最后修改时间: {datetime.fromtimestamp(mtime)}")
        except Exception as e:
            print(f"保存文件时出错: {e}")
