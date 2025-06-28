import os
import math
import pandas as pd
from datetime import datetime
import requests
import re
import json
from data.est.req import est_common
import urllib.parse
import threading

class EastmoneyDailyStockFetcher:
    def __init__(self, save_dir="/tmp/stock/daily"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def get_save_path(self, secid_or_code):
        code = secid_or_code.split('.')[-1]
        return os.path.join(self.save_dir, f"{code}.pkl")

    def file_mtime_is_today(self, path):
        if not os.path.exists(path):
            return False
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        return mtime.date() == datetime.now().date()

    def get_base_url(self, symbol, market_code, period="day", adjust="qfq", start_date=None, end_date=None):
        period_dict = {"day": 101, "week": 102, "month": 103, "5min": 5, "15min": 15, "30min": 30, "60min": 60}
        adjust_dict = {"qfq": 1, "hfq": 2, "none": 0}
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "klt": period_dict[period],
            "fqt": adjust_dict[adjust],
            "secid": f"{market_code}.{symbol}",
        }
        if start_date:
            params["beg"] = start_date
        if end_date:
            params["end"] = end_date
        return "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)

    def fetch_daily(self, secid, period="day", adjust="qfq", start_date=None, end_date=None, proxy=None):
        start_date = start_date or (datetime.now() - pd.Timedelta(days=30)).strftime("%Y%m%d")
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        market_code, symbol = secid.split('.')
        url = self.get_base_url(symbol, market_code, period, adjust, start_date, end_date)
        proxies = proxy
        try:
            resp = requests.get(url, proxies=proxies, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            klines = data.get("data", {}).get("klines", [])
            if not klines:
                print(f"{secid} 没有k线数据")
                return None
            columns = [
                "日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额",
                "振幅", "涨跌幅", "涨跌额", "换手率"
            ]
            rows = [k.split(',') for k in klines]
            return pd.DataFrame(rows, columns=columns)
        except Exception as e:
            import traceback
            print(f"获取数据失败: {e}\nURL: {url}\nProxy: {proxy}")
            traceback.print_exc()
            return None

    def save_daily(self, secid, df):
        if df is not None:
            save_path = self.get_save_path(secid)
            df.to_pickle(save_path)
            print(f"{secid} 日线数据已保存到 {save_path}")

    def update_all_daily(
        self, secids, period="day", adjust="qfq", start_date=None, end_date=None,
        use_proxy_and_concurrent=10, progress_counter=None
    ):
        # 过滤出需要更新的 secid
        secids = [secid for secid in secids if est_common.need_update(self.get_save_path(secid.split('.')[-1]))]
        if not secids:
            print("所有本地数据均为最新，无需更新")
            return

        total = len(secids)
        if progress_counter is not None:
            progress_counter["total"] = total
            progress_counter["count"] = 0

        # chunk_size 至少为 5
        chunk_size = max(5, math.ceil(total / use_proxy_and_concurrent)) if use_proxy_and_concurrent > 0 else total
        chunks = [secids[i:i + chunk_size] for i in range(0, total, chunk_size)]

        def worker(chunk):
            proxy = est_common.get_proxy()
            for secid in chunk:
                retry = 0
                max_retries = 3
                while retry < max_retries:
                    df = self.fetch_daily(secid, period, adjust, start_date, end_date, proxy=proxy)
                    if df is not None:
                        break
                    retry += 1
                    print(f"{secid} 第{retry}次尝试更换代理")
                    proxy = est_common.get_proxy()
                if df is None:
                    print(f"{secid} 更换三次代理后仍然失败，跳过")
                    if progress_counter is not None:
                        progress_counter["count"] += 1
                    return
                if df is not None:
                    self.save_daily(secid, df)
                if progress_counter is not None:
                    progress_counter["count"] += 1
                    print(f"进度: {progress_counter['count']}/{progress_counter['total']} 完成 {secid}")

        threads = []
        for chunk in chunks:
            t = threading.Thread(target=worker, args=(chunk,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def update_daily_batch(self, codes_df, period="day", adjust="qfq", start_date=None, end_date=None, use_proxy_and_concurrent=10):
        secids = codes_df['secid'].tolist()
        self.update_all_daily(secids, period, adjust, start_date, end_date, use_proxy_and_concurrent)

    def update_daily_by_df(self, codes_df, period="day", adjust="qfq", start_date=None, end_date=None, use_proxy_and_concurrent=10):
        self.update_daily_batch(codes_df, period, adjust, start_date, end_date, use_proxy_and_concurrent)

    def get_daily_df(self, code):
        """读取本地日线数据"""
        path = self.get_save_path(code)
        if os.path.exists(path):
            return pd.read_pickle(path)
        print(f"{code} 本地数据不存在: {path}")
        return None

    def get_multi_daily_df(self, codes):
        """批量读取本地日线数据"""
        return [self.get_daily_df(code) for code in codes]

if __name__ == "__main__":
    fetcher = EastmoneyDailyStockFetcher()
    all_secids = ["1.600110", "0.000001"]
    fetcher.update_all_daily(all_secids, period="day", adjust="qfq", start_date="20240601", end_date="20240620", use_proxy_and_concurrent=10)
    df = fetcher.get_daily_df("600110")
    print(df)
    dfs = fetcher.get_multi_daily_df(["600110", "000001"])
    for df in dfs:
        print(df)
