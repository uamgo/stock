import os
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import io

class SinaMinuteFetcher:
    def __init__(self, codes_path="/tmp/stock/base/all_codes.pkl", save_dir="/tmp/stock/base/minute"):
        self.codes_path = codes_path
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    async def fetch_minute_data(self, symbol):
        url = f"https://quotes.sina.cn/cn/api/jsonp_v2.php/=/CN_MarketDataService.getKLineData?symbol={symbol}&scale=1&ma=1&datalen=240"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            content = await page.content()
            await browser.close()
            start = content.find('(')
            end = content.rfind(')')
            if start == -1 or end == -1:
                print(f"{symbol} 未找到分钟数据")
                return None
            json_str = content[start+1:end]
            try:
                df = pd.read_json(io.StringIO(json_str))
                return df
            except Exception as e:
                print(f"{symbol} 分钟线解析失败: {e}")
                return None

    def minute_to_daily(self, df):
        if df is None or df.empty:
            return None
        df['date'] = df['day'].str[:10]
        grouped = df.groupby('date')
        daily = pd.DataFrame()
        daily['open'] = grouped['open'].first().astype(float)
        daily['close'] = grouped['close'].last().astype(float)
        daily['high'] = grouped['high'].max().astype(float)
        daily['low'] = grouped['low'].min().astype(float)
        daily['volume'] = grouped['volume'].apply(lambda x: x.astype(float).sum())
        daily = daily.reset_index()
        return daily

    def get_recent_5min_df(self, df):
        if df is None or df.empty:
            return None
        df['datetime'] = pd.to_datetime(df['day'])
        now = datetime.now()
        five_min_ago = now - timedelta(minutes=5)
        recent_df = df[df['datetime'] >= five_min_ago]
        return recent_df

    def has_downward_trend(self, df, window=3):
        if df is None or len(df) < window + 1:
            return False
        closes = df['close'].astype(float)
        ma = closes.rolling(window=window).mean()
        ma = ma.dropna()
        if len(ma) < 2:
            return False
        return all(x > y for x, y in zip(ma, ma[1:]))

    async def update_all(self, force_update=False):
        codes_df = pd.read_pickle(self.codes_path)
        code_col = "code" if "code" in codes_df.columns else "股票代码"
        codes = codes_df[code_col].drop_duplicates().tolist()
        downward_stocks = []
        for idx, code in enumerate(codes, 1):
            await self.update_one(code, idx, len(codes), downward_stocks, force_update=force_update)
        print("最近5分钟有下降趋势的股票：", downward_stocks)

    async def update_one(self, symbol, idx=1, total=1, downward_stocks=None, force_update=False):
        symbol_full = symbol if symbol.startswith("sh") or symbol.startswith("sz") else f"sz{symbol}"
        daily_path = os.path.join(self.save_dir, f"{symbol_full}_daily.pkl")
        recent_path = os.path.join(self.save_dir, f"{symbol_full}_recent10min.pkl")

        # 如果不强制更新且文件已存在则跳过
        if not force_update and os.path.exists(daily_path) and os.path.exists(recent_path):
            print(f"[{idx}/{total}] {symbol_full} 已存在，跳过")
            return

        df_minute = await self.fetch_minute_data(symbol_full)
        if df_minute is None or df_minute.empty:
            return
        # 只保存最后一天的日数据
        df_daily = self.minute_to_daily(df_minute)
        if df_daily is not None and not df_daily.empty:
            last_day = df_daily.iloc[[-1]]
        else:
            last_day = pd.DataFrame()
        last_day.to_pickle(daily_path)
        print(last_day)
        print(f"[{idx}/{total}] {symbol_full} 日线数据已保存，{0 if last_day is None else len(last_day)} 天")
        # 最近10分钟数据
        df_minute['datetime'] = pd.to_datetime(df_minute['day'])
        ten_min_ago = datetime.now() - timedelta(minutes=10)
        df_recent = df_minute[df_minute['datetime'] >= ten_min_ago]
        if df_recent is not None and not df_recent.empty:
            df_recent.to_pickle(recent_path)
            if downward_stocks is not None and self.has_downward_trend(df_recent):
                downward_stocks.append(symbol_full)
        else:
            pd.DataFrame().to_pickle(recent_path)

if __name__ == "__main__":
    fetcher = SinaMinuteFetcher()
    # 默认全部，不强制更新
    # asyncio.run(fetcher.update_all())
    # # 只更新指定symbol，强制更新
    asyncio.run(fetcher.update_one("sh601567", force_update=True))