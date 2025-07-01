import os
import math
import pandas as pd
from datetime import datetime
import re
import json
import urllib.parse
import requests
from data.est.req import est_common
import traceback
import threading

class EastmoneyMinuteStockFetcher:
    def __init__(self, save_dir: str = "/tmp/stock/minute"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        # 初始化进度计数器
        self.progress_counter = {"count": 0, "total": 0}

    def get_save_path(self, code: str, period: str = "1") -> str:
        return os.path.join(self.save_dir, f"{code}_{period}min.pkl")

    def file_mtime_is_today(self, path: str) -> bool:
        return os.path.exists(path) and datetime.fromtimestamp(os.path.getmtime(path)).date() == datetime.now().date()

    def get_base_url(self, symbol: str, period: str = "1", adjust: str = "", start_date=None, end_date=None) -> str:
        market_code = "1" if symbol.startswith("6") else "0"
        adjust_map = {"": "0", "qfq": "1", "hfq": "2"}
        params = {
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "secid": f"{market_code}.{symbol}",
        }
        if period == "1":
            url = "https://push2his.eastmoney.com/api/qt/stock/trends2/get"
            params.update({
                "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
                "ndays": "5",
                "iscr": "0",
            })
        else:
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params.update({
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": period,
                "fqt": adjust_map.get(adjust, "0"),
                "beg": start_date or "0",
                "end": end_date or "20500000",
            })
        return url + "?" + urllib.parse.urlencode(params)

    def fetch_minute(self, symbol: str, period: str = "1", adjust: str = "", start_date=None, end_date=None, proxy=None) -> pd.DataFrame | None:
        url = self.get_base_url(symbol, period, adjust, start_date, end_date)
        proxies = proxy
        # print(f"url: {url}")
        try:
            resp = requests.get(url, proxies=proxies, timeout=30)
            resp.encoding = "utf-8"
            text = resp.text
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if not match:
                print(f"{symbol} 未找到有效数据")
                return None
            data = json.loads(match.group(1))
            if period == "1":
                trends = data.get("data", {}).get("trends", [])
                if not trends:
                    print(f"{symbol} 没有分时数据")
                    return None
                columns = ["时间", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "均价"]
                rows = [item.split(",") for item in trends]
            else:
                klines = data.get("data", {}).get("klines", [])
                if not klines:
                    print(f"{symbol} 没有分钟K线数据")
                    return None
                columns = [
                    "时间", "开盘", "收盘", "最高", "最低", "成交量", "成交额",
                    "振幅", "涨跌幅", "涨跌额", "换手率"
                ]
                rows = [item.split(",") for item in klines]
            df = pd.DataFrame(rows, columns=columns)
            num_cols = [col for col in columns if col != "时间"]
            df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
            df["时间"] = pd.to_datetime(df["时间"], errors="coerce").astype(str)
            if period != "1":
                select_cols = [
                    "时间", "开盘", "收盘", "最高", "最低", "涨跌幅", "涨跌额",
                    "成交量", "成交额", "振幅", "换手率"
                ]
                df = df[[col for col in select_cols if col in df.columns]]
            return df
        except Exception as e:
            print(f"{symbol} 获取数据异常: {e}, proxy: {proxy}")
            return None

    def save_minute(self, symbol: str, period: str, df: pd.DataFrame):
        save_path = self.get_save_path(symbol, period)
        if df is not None:
            df.to_pickle(save_path)
            # print(f"{symbol} {period}min 分时数据已保存到 {save_path}")

    def update_all_minute(self, symbols: list[str], period: str = "1", adjust: str = "", start_date=None, end_date=None, use_proxy_and_concurrent: int = 10, progress_counter=None):
        if progress_counter is None:
            progress_counter = self.progress_counter
        progress_counter["total"] = len(symbols)
        progress_counter["count"] = 0

        symbols = [s for s in symbols if est_common.need_update(self.get_save_path(s, period))]
        if not symbols:
            print(f"所有数据均为最新，无需更新。数据目录: {self.save_dir}")
            return
        # chunk_size 至少为 40
        chunk_size = max(40, math.ceil(len(symbols) / use_proxy_and_concurrent)) if use_proxy_and_concurrent > 0 else len(symbols)
        chunks = [symbols[i:i + chunk_size] for i in range(0, len(symbols), chunk_size)]

        def worker(chunk):
            proxy = est_common.get_proxy()
            for idx, symbol in enumerate(chunk):
                retry = 0
                while retry < 3:
                    try:
                        df = self.fetch_minute(symbol, period, adjust, start_date, end_date, proxy=proxy)
                        if df is not None:
                            break
                        else:
                            print(f"{symbol} 第{retry+1}次尝试失败，切换代理重试...")
                            proxy = est_common.get_proxy()
                            retry += 1
                    except Exception as e:
                        print(f"{symbol} fetch_minute 调用异常: {e}")
                        if retry == 2:
                            traceback.print_exc()
                        proxy = est_common.get_proxy()
                        retry += 1
                if df is not None:
                    self.save_minute(symbol, period, df)
                else:
                    print(f"{symbol} 三次更换代理均失败，跳过。")
                if progress_counter is not None:
                    progress_counter["count"] += 1
                    # 每20个symbol打印一次进度
                    if progress_counter["count"] % 20 == 0 or progress_counter["count"] == progress_counter["total"]:
                        print(f"[{threading.current_thread().name}] 进度: {progress_counter['count']}/{progress_counter['total']} 完成 {symbol}")

        threads = []
        for chunk in chunks:
            t = threading.Thread(target=worker, args=(chunk,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def update_minute_batch(self, codes_df: pd.DataFrame, period: str = "1", adjust: str = "", start_date=None, end_date=None, use_proxy_and_concurrent: int = 10):
        symbols = codes_df['symbol'].tolist()
        self.update_all_minute(symbols, period, adjust, start_date, end_date, use_proxy_and_concurrent)

    def update_minute_by_df(self, codes_df: pd.DataFrame, period: str = "1", adjust: str = "", start_date=None, end_date=None, use_proxy_and_concurrent: int = 10):
        self.update_minute_batch(codes_df, period, adjust, start_date, end_date, use_proxy_and_concurrent)

    def get_minute_df(self, symbol: str, period: str = "1") -> pd.DataFrame | None:
        save_path = self.get_save_path(symbol, period)
        if os.path.exists(save_path):
            return pd.read_pickle(save_path)
        return None

    def get_multi_minute_df(self, symbols: list[str], period: str = "1") -> list[pd.DataFrame]:
        return [self.get_minute_df(symbol, period) for symbol in symbols]

if __name__ == "__main__":
    fetcher = EastmoneyMinuteStockFetcher()
    all_symbols = ["600110", "000001"]
    fetcher.update_all_minute(all_symbols, start_date="20240601", end_date="20240620", use_proxy_and_concurrent=5)
    df = fetcher.get_minute_df("600110")
    print(df)
    dfs = fetcher.get_multi_minute_df(["600110", "000001"])
    for df in dfs:
        print(df.head())
