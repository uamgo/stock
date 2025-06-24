import asyncio
import os
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright
from est_common import fetch_all_pages, get_proxy

class EastmoneyConceptStockFetcher:
    def __init__(self, save_dir="/tmp/stock/base", playwright=None):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.save_path = os.path.join(self.save_dir, "eastmoney_concept_stocks.pkl")
        proxy_info = get_proxy()
        self.proxy = (
            {
                "server": proxy_info.get("proxy"),
                "username": proxy_info.get("username"),
                "password": proxy_info.get("password"),
            }
            if proxy_info else None
        )
        self.playwright = playwright

    async def fetch_concept_stocks(self):
        base_url = (
            "https://push2.eastmoney.com/api/qt/clist/get"
            "?cb=json"
            "&fid=f62&po=1&pz=5000&pn={page}&np=1&fltt=2&invt=2"
            "&ut=8dec03ba335b81bf4ebdf7b29ec27d15"
            "&fs=m%3A90+t%3A3"
            "&fields=f12%2Cf14%2Cf2%2Cf3%2Cf62%2Cf184%2Cf66%2Cf69%2Cf72%2Cf75%2Cf78%2Cf81%2Cf84%2Cf87%2Cf204%2Cf205%2Cf124%2Cf1%2Cf13"
        )
        if self.playwright is None:
            raise RuntimeError("playwright 实例未传入")
        launch_args = {"headless": True}
        if self.proxy:
            launch_args["proxy"] = self.proxy
        async with await self.playwright.chromium.launch(**launch_args) as browser:
            page_obj = await browser.new_page()
            all_rows, _ = await fetch_all_pages(page_obj, base_url)
        if all_rows:
            df = pd.DataFrame(all_rows)
            df = df.rename(columns={
                "f12": "代码",
                "f14": "名称",
                "f3": "涨跌幅",
                "f184": "概念名称"
            })
            return df
        print("未获取到概念股数据")
        return None

    def save_df(self, df):
        if df is not None:
            if "涨跌幅" in df.columns:
                df = df.sort_values(by="涨跌幅", ascending=False).reset_index(drop=True)
            df.to_pickle(self.save_path)
            print(f"已保存到 {self.save_path}")

    def file_mtime_is_today(self, path):
        if not os.path.exists(path):
            return False
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        return mtime.date() == datetime.now().date()

    async def fetch_and_save(self, force_update=False):
        print(f"概念股文件将保存到: {self.save_path}")
        if not force_update and os.path.exists(self.save_path) and self.file_mtime_is_today(self.save_path):
            print(f"{self.save_path} 已是今日文件，无需更新。")
            return pd.read_pickle(self.save_path)
        df = await self.fetch_concept_stocks()
        if df is not None:
            self.save_df(df)
        return df

    def get_concept_df(self):
        """
        读取本地保存的概念股数据 DataFrame。
        """
        if os.path.exists(self.save_path):
            return pd.read_pickle(self.save_path)
        print(f"{self.save_path} 文件不存在，请先运行 fetch_and_save() 获取数据。")
        return None

if __name__ == "__main__":
    async def main():
        async with async_playwright() as playwright:
            fetcher = EastmoneyConceptStockFetcher(playwright=playwright)
            df = await fetcher.fetch_and_save(force_update=True)
            if df is not None:
                print(df.head(10))
                print(f"总计拿到的行数: {len(df)}")
            else:
                print("未获取到数据")
    asyncio.run(main())
