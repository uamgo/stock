import asyncio
import os
import math
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
from data.est import est_common

class ConceptStockManager:
    def __init__(self, save_dir="/tmp/stock/concept", playwright=None):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.playwright = playwright

    def get_save_path(self, concept_code: str) -> str:
        return os.path.join(self.save_dir, f"{concept_code}.pkl")

    def file_mtime_is_today(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        return mtime.date() == datetime.now().date()

    def get_base_url(self, concept_code: str) -> str:
        return (
            "https://push2.eastmoney.com/api/qt/clist/get"
            "?cb=json"
            "&fid=f62&po=1&pz=50&pn=1&np=1&fltt=2&invt=2"
            "&ut=8dec03ba335b81bf4ebdf7b29ec27d15"
            f"&fs=b%3A{concept_code}"
            "&fields=f12%2Cf14%2Cf2%2Cf3%2Cf62%2Cf184%2Cf66%2Cf69%2Cf72%2Cf75%2Cf78%2Cf81%2Cf84%2Cf87%2Cf204%2Cf205%2Cf124%2Cf1%2Cf13"
        )

    async def fetch_concept_members(self, concept_code: str, proxy=None) -> pd.DataFrame:
        base_url = self.get_base_url(concept_code)
        if self.playwright is None:
            raise RuntimeError("playwright 实例未传入")
        launch_args = {"headless": True}
        if proxy:
            launch_args["proxy"] = proxy
        async with await self.playwright.chromium.launch(**launch_args) as browser:
            page_obj = await browser.new_page()
            all_rows, _ = await est_common.fetch_all_pages(page_obj, base_url)
            await page_obj.close()
        if all_rows:
            df = pd.DataFrame(all_rows).rename(
                columns={"f12": "代码", "f14": "名称", "f3": "涨跌幅", "f13": "前缀"}
            )
            df["涨跌幅"] = pd.to_numeric(df["涨跌幅"], errors="coerce")
            return df.sort_values(by="涨跌幅", ascending=False).reset_index(drop=True)
        return None

    def save_concept_members(self, concept_code: str, df: pd.DataFrame):
        if df is not None:
            df.to_pickle(self.get_save_path(concept_code))

    async def _update_concepts_async(self, concept_codes, use_proxy_and_concurrent=10, progress_counter=None):
        if use_proxy_and_concurrent <= 0:
            chunked_codes = [concept_codes]
        else:
            chunk_size = math.ceil(len(concept_codes) / use_proxy_and_concurrent)
            chunked_codes = [concept_codes[i:i + chunk_size] for i in range(0, len(concept_codes), chunk_size)]

        async def fetch_chunk(codes_chunk):
            proxy_info = est_common.get_proxy()
            proxy = (
                {
                    "server": proxy_info.get("proxy"),
                    "username": proxy_info.get("username"),
                    "password": proxy_info.get("password"),
                }
                if proxy_info else None
            )
            if self.playwright is None:
                raise RuntimeError("playwright 实例未传入")
            launch_args = {"headless": True}
            if proxy:
                launch_args["proxy"] = proxy
            async with await self.playwright.chromium.launch(**launch_args) as browser:
                for code in codes_chunk:
                    save_path = self.get_save_path(code)
                    if not est_common.need_update_simple(save_path):
                        if progress_counter is not None:
                            progress_counter["count"] += 1
                        continue
                    try:
                        df = await self.fetch_concept_members(code, proxy=None)
                        self.save_concept_members(code, df)
                        if progress_counter is not None:
                            progress_counter["count"] += 1
                    except Exception as e:
                        print(f"更新概念 {code} 失败: {e}")

        await asyncio.gather(*(fetch_chunk(chunk) for chunk in chunked_codes))

    async def update_all_concepts(self, concept_codes, use_proxy_and_concurrent=10):
        progress_counter = {"count": 0, "total": len(concept_codes)}
        await self._update_concepts_async(concept_codes, use_proxy_and_concurrent, progress_counter)

    async def update_concepts_batch(self, codes_df: pd.DataFrame, use_proxy_and_concurrent=10):
        codes = codes_df['code'].tolist()
        await self.update_all_concepts(codes, use_proxy_and_concurrent)

    async def update_concepts_by_df(self, codes_df: pd.DataFrame, use_proxy_and_concurrent=10):
        await self.update_concepts_batch(codes_df, use_proxy_and_concurrent)

    def get_concept_df(self, concept_code: str) -> pd.DataFrame:
        path = self.get_save_path(concept_code)
        if os.path.exists(path):
            return pd.read_pickle(path)
        print(f"{path} 文件不存在，请先运行 update_all_concepts 获取数据。")
        return None

    def get_members_codes(self, concept_codes) -> pd.DataFrame:
        dfs = []
        for code in concept_codes:
            df = self.get_concept_df(code)
            if df is not None:
                df = df[["代码", "名称"]].copy()
                df["concept_code"] = code
                dfs.append(df)
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        return pd.DataFrame(columns=["代码", "名称", "concept_code"])

if __name__ == "__main__":
    async def main():
        async with async_playwright() as playwright:
            manager = ConceptStockManager(playwright=playwright)
            all_concept_codes = ['BK0816', 'BK1051', 'BK0983', 'BK1071', 'BK1152', 'BK0883', 'BK0603', 'BK1075', 'BK0606', 'BK0818']
            await manager._update_concepts_async(all_concept_codes, use_proxy_and_concurrent=2, progress_counter={"count": 0, "total": len(all_concept_codes)})
            df = manager.get_concept_df("BK0816")
            print(df)
            codes_df = manager.get_members_codes(["BK0816", "BK0817"])
            print(codes_df)
    asyncio.run(main())
