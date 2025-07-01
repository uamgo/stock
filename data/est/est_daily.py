import os
import math
import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
import re
import json
from data.est import est_common
import urllib.parse

class EastmoneyDailyStockFetcher:
    def __init__(self, save_dir="/tmp/stock/daily", playwright=None):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.playwright = playwright

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

    async def fetch_daily(self, secid, period="day", adjust="qfq", start_date=None, end_date=None, proxy=None):
        if self.playwright is None:
            raise RuntimeError("playwright 实例未传入")
        start_date = start_date or (datetime.now() - pd.Timedelta(days=30)).strftime("%Y%m%d")
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        market_code, symbol = secid.split('.')
        url = self.get_base_url(symbol, market_code, period, adjust, start_date, end_date)
        launch_args = {"headless": True}
        if proxy:
            launch_args["proxy"] = proxy
        browser = await self.playwright.chromium.launch(**launch_args)
        try:
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=10000)
                await page.wait_for_load_state('networkidle')
                content = await page.content()
            except Exception as e:
                print(f"页面加载失败: {e}\nURL: {url}")
                return None
            return self._parse_page_content(content, secid, url)
        finally:
            await browser.close()

    def _parse_page_content(self, content, secid, url):
        match = re.search(r'<pre.*?>(.*?)</pre>', content, re.DOTALL)
        if not match:
            print(f"未找到有效数据\nURL: {url}\nContent: {content[:1000]}")
            return None
        try:
            data = json.loads(match.group(1))
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
            print(f"解析数据失败: {e}")
            return None

    def save_daily(self, secid, df):
        if df is not None:
            save_path = self.get_save_path(secid)
            df.to_pickle(save_path)
            print(f"{secid} 日线数据已保存到 {save_path}")

    def fetch_and_save_daily(self, secid, period="day", adjust="qfq", start_date=None, end_date=None, proxy=None):
        df = asyncio.run(self.fetch_daily(secid, period, adjust, start_date, end_date, proxy=proxy))
        if df is not None:
            self.save_daily(secid, df)
        return df

    async def _fetch_daily_with_page(self, page, secid, period="day", adjust="qfq", start_date=None, end_date=None):
        start_date = start_date or (datetime.now() - pd.Timedelta(days=30)).strftime("%Y%m%d")
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        market_code, symbol = secid.split('.')
        url = self.get_base_url(symbol, market_code, period, adjust, start_date, end_date)
        try:
            await page.goto(url, timeout=10000)
            await asyncio.sleep(1.5)
            content = await page.content()
        except Exception as e:
            print(f"页面加载失败: {e}\nURL: {url}")
            return None
        return self._parse_page_content(content, secid, url)

    async def _update_daily_async(self, secids, period="day", adjust="qfq", start_date=None, end_date=None, concurrency=10, progress_counter=None):
        import threading

        async def fetch_chunk(secid_chunk):
            proxy_info = est_common.get_proxy()
            proxy = (
                {
                    "server": proxy_info.get("proxy"),
                    "username": proxy_info.get("username"),
                    "password": proxy_info.get("password"),
                }
                if proxy_info else None
            )
            print(f"[Thread-{threading.get_ident()}][EastmoneyDailyStockFetcher] 分片线程使用独立代理: {proxy}")
            launch_args = {"headless": True}
            if proxy:
                launch_args["proxy"] = proxy
            async with async_playwright() as p:
                browser = await p.chromium.launch(**launch_args)
                try:
                    skip_count = 0
                    for secid in secid_chunk:
                        code = secid.split('.')[-1]
                        save_path = self.get_save_path(code)
                        if not est_common.need_update(save_path):
                            print(f"{code} 本地数据已是最新，跳过更新")
                            continue
                        page = await browser.new_page()
                        try:
                            df = await self._fetch_daily_with_page(page, secid, period, adjust, start_date, end_date)
                            if df is None:
                                print(f"{secid} 获取数据失败，尝试重新获取代理并重试")
                                proxy_info = est_common.get_proxy()
                                proxy = (
                                    {
                                        "server": proxy_info.get("proxy"),
                                        "username": proxy_info.get("username"),
                                        "password": proxy_info.get("password"),
                                    }
                                    if proxy_info else None
                                )
                                await page.close()
                                page = await browser.new_page()
                                try:
                                    df = await self._fetch_daily_with_page(page, secid, period, adjust, start_date, end_date)
                                finally:
                                    await page.close()
                            if df is None:
                                print(f"{secid} 仍然获取失败，跳过")
                                skip_count += 1
                                if skip_count > 3:
                                    print(f"跳过 {secid}，连续失败超过3次")
                                    break
                                else:
                                    continue
                            self.save_daily(secid, df)
                            if progress_counter is not None:
                                progress_counter["count"] += 1
                                print(f"[Thread-{threading.get_ident()}][EastmoneyDailyStockFetcher] 进度: {progress_counter['count']}/{progress_counter['total']} 完成 {secid}")
                        finally:
                            await page.close()
                finally:
                    await browser.close()

        if concurrency <= 0:
            chunks = [secids]
        else:
            chunk_size = math.ceil(len(secids) / concurrency)
            chunks = [secids[i:i + chunk_size] for i in range(0, len(secids), chunk_size)]

        await asyncio.gather(*(fetch_chunk(chunk) for chunk in chunks))

    async def update_all_daily(
        self, secids, period="day", adjust="qfq", start_date=None, end_date=None,
        use_proxy_and_concurrent=10, progress_counter=None
    ):
        await self._update_daily_async(
            secids, period, adjust, start_date, end_date, use_proxy_and_concurrent, progress_counter
        )

    def update_daily_batch(self, codes_df, period="day", adjust="qfq", start_date=None, end_date=None, use_proxy_and_concurrent=10):
        secids = codes_df['secid'].tolist()
        asyncio.run(self.update_all_daily(secids, period, adjust, start_date, end_date, use_proxy_and_concurrent))

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
    asyncio.run(fetcher.update_all_daily(all_secids, period="day", adjust="qfq", start_date="20240601", end_date="20240620", use_proxy_and_concurrent=10))
    df = fetcher.get_daily_df("600110")
    print(df)
    dfs = fetcher.get_multi_daily_df(["600110", "000001"])
    for df in dfs:
        print(df)
