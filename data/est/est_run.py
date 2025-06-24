import os
from datetime import datetime, time
import pandas as pd
import re
from typing import List
import asyncio
from playwright.async_api import async_playwright

from est_concept import EastmoneyConceptStockFetcher
from est_concept_codes import ConceptStockManager
from est_daily import EastmoneyDailyStockFetcher
from est_minute import EastmoneyMinuteStockFetcher
from est_common import init_async_playwright, close_async_playwright
import traceback
import exchange_calendars as xcals


FILTER_WORDS = ['*ST', 'ST', '退市', 'N', 'L', 'C', 'U', 'bj', 'BJ']
FILTER_PATTERN = re.compile('|'.join(map(re.escape, FILTER_WORDS)), re.IGNORECASE)
BLACKLIST_PATH = "/Users/kevin/Downloads/blacklist_codes.txt"

def is_trading_day():
    # 简单判断：周一到周五为交易日，实际可用交易所日历替换
    # 使用 exchange_calendars 判断是否交易日
    cal = xcals.get_calendar("XSHG")
    today = pd.Timestamp(datetime.now().date())
    return cal.is_session(today)

def is_after_1130():
    now = datetime.now().time()
    return now >= time(11, 30)

def read_blacklist(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def write_blacklist(path, codes):
    with open(path, "w", encoding="utf-8") as f:
        for code in sorted(codes):
            f.write(f"{code}\n")

class EstStockPipeline:
    def __init__(self, top_n: int = 10, use_proxy: bool = False, playwright=None):
        self.top_n = top_n
        self.use_proxy = use_proxy
        self.playwright = playwright
        self.concept_manager = ConceptStockManager(playwright=playwright)
        self.daily_fetcher = EastmoneyDailyStockFetcher(playwright=playwright)
        self.minute_fetcher = EastmoneyMinuteStockFetcher(playwright=playwright)

    async def get_top_n_concepts(self):
        fetcher = EastmoneyConceptStockFetcher(playwright=self.playwright)
        df = await fetcher.fetch_and_save(force_update=True)
        if df is None:
            raise RuntimeError("未能获取概念板块数据")
        return df.nlargest(self.top_n, "涨跌幅")["代码"].tolist()

    def update_top_n_concept_members(self, concept_codes: List[str]) -> None:
        concurrent = 10 if self.use_proxy else 10  # 默认10
        self.concept_manager.update_all_concepts(concept_codes, use_proxy_and_concurrent=concurrent)

    def get_all_members(self, concept_codes: List[str]) -> pd.DataFrame:
        dfs = [self.concept_manager.get_concept_df(code) for code in concept_codes]
        dfs = [df for df in dfs if df is not None]
        if not dfs:
            return pd.DataFrame()
        all_df = pd.concat(dfs, ignore_index=True)
        mask = ~all_df["名称"].str.contains(FILTER_PATTERN, na=False) & \
               ~all_df["代码"].str.contains(FILTER_PATTERN, na=False)
        return all_df[mask].drop_duplicates(subset=["代码"])

    async def update_daily_for_members(self, members_df):
        secids = (members_df["前缀"].astype(str) + '.' + members_df["代码"].astype(str)).tolist()
        if not members_df.empty:
            print("第一行字段名和值：")
            for col in members_df.columns:
                print(f"{col}: {members_df.iloc[0][col]}")
        await self.daily_fetcher.update_all_daily(
            secids, period="day", adjust="qfq", use_proxy_and_concurrent=self.top_n  
        )

    async def update_minute_for_members(self, members_df: pd.DataFrame) -> None:
        codes_df = pd.DataFrame({"symbol": members_df["代码"].tolist()})
        await self.minute_fetcher.update_minute_batch(codes_df, period="1", use_proxy_and_concurrent=self.top_n)

    def select_up_stocks(self, members_df: pd.DataFrame) -> pd.DataFrame:
        result = []
        for code in members_df["代码"]:
            daily_df = self.daily_fetcher.get_daily_df(code)
            if daily_df is None or daily_df.empty or len(daily_df) < 20:
                continue
            last_daily = daily_df.iloc[-1]
            try:
                pct_chg = float(last_daily.get("涨跌幅", 0))
            except Exception:
                pct_chg = 0
            vol = pd.to_numeric(daily_df["成交量"], errors="coerce")
            if vol.isnull().any():
                continue
            today_vol = vol.iloc[-1]
            max_vol_20 = vol[-20:].max()
            if today_vol >= max_vol_20:
                result.append({
                    "代码": code,
                    "名称": last_daily.get("名称", ""),
                    "涨跌幅": pct_chg,
                    "今日成交量": today_vol,
                    "20日最大量": max_vol_20
                })
        return pd.DataFrame(result)

    async def run(self):
        self.top_n = 20  # 默认获取前20个概念板块
        top_concept_codes = await self.get_top_n_concepts()
        print("Top N 概念板块代码:", top_concept_codes)
        # 读取黑名单并排除
        if is_trading_day() and is_after_1130():
            blacklist_codes = read_blacklist(BLACKLIST_PATH)
            top_concept_codes = [code for code in top_concept_codes if code not in blacklist_codes]
        await self.concept_manager.update_all_concepts(top_concept_codes, use_proxy_and_concurrent=10)  # 默认10
        members_df = self.get_all_members(top_concept_codes)
        print(f"过滤后成分股数量: {len(members_df)}")
        await self.update_daily_for_members(members_df)
        await self.update_minute_for_members(members_df)
        up_df = self.select_up_stocks(members_df)
        print("放量上涨且涨幅大于3%的股票：")
        print(up_df)

        # ====== 新增黑名单处理逻辑 ======
        if is_trading_day() and is_after_1130():
            # 获取所有成分股代码
            all_codes = top_concept_codes
            # 获取被过滤掉的代码
            filtered_codes = set()
            for code in all_codes:
                if code not in up_df["代码"].astype(str).tolist():
                    filtered_codes.add(code)
            # 合并已有黑名单
            if os.path.exists(BLACKLIST_PATH):
                # 判断是否今天11:30生成（通过文件修改时间）
                mtime = datetime.fromtimestamp(os.path.getmtime(BLACKLIST_PATH))
                now = datetime.now()
                if mtime.date() == now.date() and mtime.hour == 11 and mtime.minute == 30:
                    old_codes = read_blacklist(BLACKLIST_PATH)
                    filtered_codes = filtered_codes.union(old_codes)
            # 写入黑名单
            write_blacklist(BLACKLIST_PATH, filtered_codes)
            print(f"已将{len(filtered_codes)}只股票写入黑名单：{BLACKLIST_PATH}")
        # ====== 黑名单处理逻辑结束 ======

        return up_df

# 主入口
if __name__ == "__main__":
    import asyncio
    from playwright.async_api import async_playwright

    async def main():
        async with async_playwright() as playwright:
            pipeline = EstStockPipeline(playwright=playwright)
            up_df = await pipeline.run()
            if not up_df.empty:
                codes_str = ','.join(up_df["代码"].astype(str).tolist())
                with open("/Users/kevin/Downloads/up_stocks_codes.txt", "w", encoding="utf-8") as f:
                    f.write(codes_str)
                print(f"已将股票代码写入 /Users/kevin/Downloads/up_stocks_codes.txt")
            else:
                print("没有符合条件的股票。")
    asyncio.run(main())
