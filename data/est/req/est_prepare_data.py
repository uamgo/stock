import os
import re
import traceback
from datetime import datetime, time
from typing import List
from pathlib import Path
import asyncio
import time

import pandas as pd
import exchange_calendars as xcals
from data.est.req.est_concept import EastmoneyConceptStockFetcher
from data.est.req.est_concept_codes import ConceptStockManager
from data.est.req.est_daily import EastmoneyDailyStockFetcher
from data.est.req.est_minute import EastmoneyMinuteStockFetcher
from data.est.req import est_common

FILTER_WORDS = ['*ST', 'ST', '退市', 'N', 'L', 'C', 'U', 'bj', 'BJ', '688', '83', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99']
FILTER_PATTERN = re.compile('|'.join(map(re.escape, FILTER_WORDS)), re.IGNORECASE)
DATA_DIR = Path("/tmp/stock/est_prepare_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

BLACKLIST_PATH = str(DATA_DIR / "blacklist_codes.txt")
MEMBERS_DF_PATH = str(DATA_DIR / "members_df.pkl")

class EstStockPipeline:
    def __init__(self, top_n: int = 20, use_proxy: bool = False):
        self.top_n = top_n
        self.use_proxy = use_proxy
        self.concept_manager = ConceptStockManager()
        self.daily_fetcher = EastmoneyDailyStockFetcher()
        self.minute_fetcher = EastmoneyMinuteStockFetcher()

    async def get_top_n_concepts(self) -> List[str]:
        fetcher = EastmoneyConceptStockFetcher()
        df = fetcher.fetch_and_save()
        if df is None:
            raise RuntimeError("未能获取概念板块数据")
        return df.nlargest(self.top_n, "涨跌幅")["代码"].tolist()

    def get_all_members(self, concept_codes: List[str]) -> pd.DataFrame:
        dfs = [self.concept_manager.get_concept_df(code) for code in concept_codes]
        dfs = [df for df in dfs if df is not None]
        if not dfs:
            return pd.DataFrame()
        all_df = pd.concat(dfs, ignore_index=True)
        # 过滤掉以 FILTER_WORDS 里任一元素开头的股票
        # 过滤掉名称或代码以 FILTER_WORDS 中任一元素开头，或最新价>=100 的股票
        mask = (
            ~all_df["名称"].str.startswith(tuple(FILTER_WORDS), na=False)
            & ~all_df["代码"].str.startswith(tuple(FILTER_WORDS), na=False)
        )
        return all_df[mask].drop_duplicates(subset=["代码"])

    async def run(self) -> pd.DataFrame:
        if not est_common.need_update(MEMBERS_DF_PATH):
            mtime = os.path.getmtime(MEMBERS_DF_PATH)
            print(f"{MEMBERS_DF_PATH} 无需更新，文件最后修改时间: {datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            return None

        t0 = time.time()
        time_stats = {}

        # 获取概念板块
        t_start = time.time()
        self.top_n = 10
        top_concept_codes = await self.get_top_n_concepts()
        t_end = time.time()
        time_stats["获取概念板块"] = t_end - t_start
        print("Top N 概念板块代码:", top_concept_codes)

        # 更新概念成分
        t_start = time.time()
        self.concept_manager.update_all_concepts(
            top_concept_codes, use_proxy_and_concurrent=min(10, self.top_n)
        )
        t_end = time.time()
        time_stats["更新概念成分"] = t_end - t_start

        # 过滤并保存成分股
        t_start = time.time()
        members_df = self.get_all_members(top_concept_codes)
        est_common.save_df_to_file(members_df, MEMBERS_DF_PATH)
        t_end = time.time()
        time_stats["过滤并保存成分股"] = t_end - t_start
        print(f"过滤后成分股数量: {len(members_df)}，已保存 members_df 到 {MEMBERS_DF_PATH}")
        for idx, row in members_df.iterrows():
            print(f"代码: {row['代码']}, 名称: {row['名称']}, 股价: {row['股价']}")
        # 更新日线数据
        if not members_df.empty:
            t_start = time.time()
            await self.update_daily_for_members(members_df)
            t_end = time.time()
            time_stats["更新日线数据"] = t_end - t_start

            # 更新分钟线数据
            t_start = time.time()
            await self.update_minute_for_members(members_df)
            t_end = time.time()
            time_stats["更新分钟线数据"] = t_end - t_start

        # 打印代理使用次数
        print(f"代理使用次数: {getattr(est_common, 'PROXY_USE_COUNT', 0)}")
        total_time = time.time() - t0
        print("各阶段耗时统计：")
        for k, v in time_stats.items():
            print(f"{k}: {v:.2f} 秒")
        print(
            f"总耗时: {total_time:.2f} 秒 | 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return members_df

    async def update_daily_for_members(self, members_df: pd.DataFrame, period="day", adjust="qfq", use_proxy_and_concurrent=20):
        if members_df is None or members_df.empty:
            print("members_df 为空，跳过日线更新")
            return
        secids = [
            f"1.{code}" if str(code).startswith("6") else f"0.{code}"
            for code in members_df["代码"]
        ]
        self.daily_fetcher.update_all_daily(
            secids, period=period, adjust=adjust, use_proxy_and_concurrent=use_proxy_and_concurrent
        )
        print(f"已批量更新 {len(secids)} 只股票的日线数据")

    async def update_minute_for_members(self, members_df: pd.DataFrame, period="1", use_proxy_and_concurrent=20):
        if members_df is None or members_df.empty:
            print("members_df 为空，跳过分钟线更新")
            return
        codes_df = pd.DataFrame({"symbol": members_df["代码"].tolist()})
        self.minute_fetcher.update_minute_batch(
            codes_df, period=period, use_proxy_and_concurrent=use_proxy_and_concurrent
        )
        print(f"已批量更新 {len(codes_df)} 只股票的分钟数据")

def load_members_df_from_path() -> pd.DataFrame:
    try:
        return est_common.load_df_from_file(MEMBERS_DF_PATH)
    except Exception as e:
        print(f"读取 {MEMBERS_DF_PATH} 失败: {e}")
        return pd.DataFrame()

async def main():
    pipeline = EstStockPipeline(top_n=20)
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
