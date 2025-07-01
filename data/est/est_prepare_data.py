import os
import re
import traceback
from datetime import datetime, time
from typing import List
from pathlib import Path

import pandas as pd
import exchange_calendars as xcals
from data.est.est_concept import EastmoneyConceptStockFetcher
from data.est.est_concept_codes import ConceptStockManager
from data.est.est_daily import EastmoneyDailyStockFetcher
from data.est.est_minute import EastmoneyMinuteStockFetcher
from data.est.est_common import save_df_to_file, load_df_from_file, need_update

FILTER_WORDS = ['*ST', 'ST', '退市', 'N', 'L', 'C', 'U', 'bj', 'BJ']
FILTER_PATTERN = re.compile('|'.join(map(re.escape, FILTER_WORDS)), re.IGNORECASE)
DATA_DIR = Path("/tmp/stock/est_prepare_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

BLACKLIST_PATH = str(DATA_DIR / "blacklist_codes.txt")
MEMBERS_DF_PATH = str(DATA_DIR / "members_df.pkl")

class EstStockPipeline:
    def __init__(self, top_n: int = 20, use_proxy: bool = False, playwright=None):
        self.top_n = top_n
        self.use_proxy = use_proxy
        self.playwright = playwright
        self.concept_manager = ConceptStockManager(playwright=playwright)
        self.daily_fetcher = EastmoneyDailyStockFetcher(playwright=playwright)
        self.minute_fetcher = EastmoneyMinuteStockFetcher(playwright=playwright)

    async def get_top_n_concepts(self) -> List[str]:
        fetcher = EastmoneyConceptStockFetcher(playwright=self.playwright)
        df = await fetcher.fetch_and_save()
        if df is None:
            raise RuntimeError("未能获取概念板块数据")
        return df.nlargest(self.top_n, "涨跌幅")["代码"].tolist()

    def get_all_members(self, concept_codes: List[str]) -> pd.DataFrame:
        dfs = [self.concept_manager.get_concept_df(code) for code in concept_codes]
        dfs = [df for df in dfs if df is not None]
        if not dfs:
            return pd.DataFrame()
        all_df = pd.concat(dfs, ignore_index=True)
        mask = ~all_df["名称"].str.contains(FILTER_PATTERN, na=False) & \
               ~all_df["代码"].str.contains(FILTER_PATTERN, na=False)
        return all_df[mask].drop_duplicates(subset=["代码"])

    async def run(self) -> pd.DataFrame:
        if not need_update(MEMBERS_DF_PATH):
            print(f"{MEMBERS_DF_PATH} 无需更新")
            return None
        top_concept_codes = await self.get_top_n_concepts()
        print("Top N 概念板块代码:", top_concept_codes)
        await self.concept_manager.update_all_concepts(
            top_concept_codes, use_proxy_and_concurrent=min(10, self.top_n)
        )
        members_df = self.get_all_members(top_concept_codes)
        save_df_to_file(members_df, MEMBERS_DF_PATH)
        print(f"过滤后成分股数量: {len(members_df)}，已保存 members_df 到 {MEMBERS_DF_PATH}")
        if not members_df.empty:
            await self.update_daily_for_members(members_df)
            await self.update_minute_for_members(members_df)
        return members_df

    async def update_daily_for_members(self, members_df: pd.DataFrame, period="day", adjust="qfq", use_proxy_and_concurrent=10):
        """
        批量更新 members_df 中所有股票的日线数据
        """
        if members_df is None or members_df.empty:
            print("members_df 为空，跳过日线更新")
            return
        secids = [
            f"1.{code}" if str(code).startswith("6") else f"0.{code}"
            for code in members_df["代码"]
        ]
        await self.daily_fetcher.update_all_daily(
            secids, period=period, adjust=adjust, use_proxy_and_concurrent=use_proxy_and_concurrent
        )
        print(f"已批量更新 {len(secids)} 只股票的日线数据")

    async def update_minute_for_members(self, members_df: pd.DataFrame, period="1", use_proxy_and_concurrent=10):
        """
        批量更新 members_df 中所有股票的分钟数据
        """
        if members_df is None or members_df.empty:
            print("members_df 为空，跳过分钟线更新")
            return
        codes_df = pd.DataFrame({"symbol": members_df["代码"].tolist()})
        await self.minute_fetcher.update_minute_batch(
            codes_df, period=period, use_proxy_and_concurrent=use_proxy_and_concurrent
        )
        print(f"已批量更新 {len(codes_df)} 只股票的分钟数据")

def load_members_df_from_path() -> pd.DataFrame:
    try:
        return load_df_from_file(MEMBERS_DF_PATH)
    except Exception as e:
        print(f"读取 {MEMBERS_DF_PATH} 失败: {e}")
        return pd.DataFrame()

async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as playwright:
        pipeline = EstStockPipeline(top_n=20, playwright=playwright)
        await pipeline.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
