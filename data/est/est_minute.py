import os
import math
import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
import re
import json
import urllib.parse
from est_common import get_proxy

class EastmoneyMinuteStockFetcher:
    def __init__(self, save_dir="/tmp/stock/minute", playwright=None):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.playwright = playwright

    def get_save_path(self, code, period="1"):
        return os.path.join(self.save_dir, f"{code}_{period}min.pkl")

    def file_mtime_is_today(self, path):
        return os.path.exists(path) and datetime.fromtimestamp(os.path.getmtime(path)).date() == datetime.now().date()

    def get_base_url(self, symbol, period="1", adjust="", start_date=None, end_date=None):
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

    async def fetch_minute(self, symbol, period="1", adjust="", start_date=None, end_date=None, proxy=None):
        url = self.get_base_url(symbol, period, adjust, start_date, end_date)
        launch_args = {"headless": True}
        if proxy:
            launch_args["proxy"] = proxy
        playwright = self.playwright
        if playwright is None:
            raise RuntimeError("playwright 实例未传入")
        browser = await playwright.chromium.launch(**launch_args)
        try:
            page = await browser.new_page()
            await page.goto(url)
            await asyncio.sleep(1)
            content = await page.content()
            match = re.search(r'<pre.*?>(\{.*?\})</pre>', content, re.DOTALL)
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
            print(f"{symbol} 获取数据异常: {e}")
            return None
        finally:
            await browser.close()

    def save_minute(self, symbol, period, df):
        save_path = self.get_save_path(symbol, period)
        if df is not None:
            df.to_pickle(save_path)
            print(f"{symbol} {period}min 分时数据已保存到 {save_path}")

    async def _update_minute_async(self, symbols, period="1", adjust="", start_date=None, end_date=None, concurrency=10, progress_counter=None):
        import threading
        if concurrency <= 0:
            chunks = [symbols]
        else:
            chunk_size = math.ceil(len(symbols) / concurrency)
            chunks = [symbols[i:i + chunk_size] for i in range(0, len(symbols), chunk_size)]

        async def fetch_chunk(symbol_chunk):
            proxy_info = get_proxy()
            proxy = (
                {
                    "server": proxy_info.get("proxy"),
                    "username": proxy_info.get("username"),
                    "password": proxy_info.get("password"),
                }
                if proxy_info else None
            )
            print(f"[Thread-{threading.get_ident()}][EastmoneyMinuteStockFetcher] 分片线程使用独立代理: {proxy}")
            for symbol in symbol_chunk:
                df = await self.fetch_minute(symbol, period, adjust, start_date, end_date, proxy=proxy)
                # 如果 df 为 None，尝试重新获取 proxy 并重试一次
                if df is None:
                    proxy_info = get_proxy()
                    proxy = (
                        {
                            "server": proxy_info.get("proxy"),
                            "username": proxy_info.get("username"),
                            "password": proxy_info.get("password"),
                        }
                        if proxy_info else None
                    )
                    print(f"[Thread-{threading.get_ident()}][EastmoneyMinuteStockFetcher] 重新获取代理后重试: {proxy}")
                    df = await self.fetch_minute(symbol, period, adjust, start_date, end_date, proxy=proxy)
                if df is None:
                    continue
                self.save_minute(symbol, period, df)
                if progress_counter is not None:
                    progress_counter["count"] += 1
                    print(f"[Thread-{threading.get_ident()}][EastmoneyMinuteStockFetcher] 进度: {progress_counter['count']}/{progress_counter['total']} 完成 {symbol}")

        await asyncio.gather(*(fetch_chunk(chunk) for chunk in chunks))

    async def update_all_minute(self, symbols, period="1", adjust="", start_date=None, end_date=None, use_proxy_and_concurrent=10, progress_counter=None):
        if progress_counter is not None:
            progress_counter["total"] = len(symbols)
            progress_counter["count"] = 0
        await self._update_minute_async(
            symbols, period, adjust, start_date, end_date, use_proxy_and_concurrent, progress_counter
        )

    async def update_minute_batch(self, codes_df, period="1", adjust="", start_date=None, end_date=None, use_proxy_and_concurrent=10):
        symbols = codes_df['symbol'].tolist()
        await self.update_all_minute(symbols, period, adjust, start_date, end_date, use_proxy_and_concurrent)

    async def update_minute_by_df(self, codes_df, period="1", adjust="", start_date=None, end_date=None, use_proxy_and_concurrent=10):
        await self.update_minute_batch(codes_df, period, adjust, start_date, end_date, use_proxy_and_concurrent)

    def get_minute_df(self, symbol, period="1"):
        save_path = self.get_save_path(symbol, period)
        if os.path.exists(save_path):
            return pd.read_pickle(save_path)
        return None

    def get_multi_minute_df(self, symbols, period="1"):
        return [self.get_minute_df(symbol, period) for symbol in symbols]

if __name__ == "__main__":
    async def main():
        fetcher = EastmoneyMinuteStockFetcher(playwright=await async_playwright().start())
        all_symbols = ["600110", "000001"]
        await fetcher.update_all_minute(all_symbols, start_date="20240601", end_date="20240620", use_proxy_and_concurrent=10)
        df = fetcher.get_minute_df("600110")
        print(df)
        dfs = fetcher.get_multi_minute_df(["600110", "000001"])
        for df in dfs:
            print(df.head())
    asyncio.run(main())
