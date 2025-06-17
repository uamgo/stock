import os
import pandas as pd
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright
import io  # 新增

class SinaDailyFetcher:
    def __init__(self, codes_path="/tmp/stock/base/all_codes.pkl", save_dir="/tmp/stock/base/daily"):
        self.codes_path = codes_path
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    async def fetch_60min_data(self, symbol):
        url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=60&ma=3&datalen=20"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            content = await page.content()
            await browser.close()
            start = content.find('[')
            end = content.rfind(']')
            if start == -1 or end == -1:
                return None
            json_str = content[start:end+1]
            try:
                df = pd.read_json(io.StringIO(json_str))  # 修正
                return df
            except Exception as e:
                print(f"{symbol} 60分钟线解析失败: {e}")
                return None

    def minute_to_daily(self, df):
        if df is None or df.empty:
            return None
        df['date'] = df['day'].str[:10]
        today = datetime.now().strftime("%Y-%m-%d")
        df = df[df['date'] != today]
        grouped = df.groupby('date')
        daily = pd.DataFrame()
        daily['open'] = grouped['open'].first().astype(float)
        daily['close'] = grouped['close'].last().astype(float)
        daily['high'] = grouped['high'].max().astype(float)
        daily['low'] = grouped['low'].min().astype(float)
        daily['volume'] = grouped['volume'].apply(lambda x: x.astype(float).sum())
        daily = daily.reset_index()
        return daily

    async def update_all(self):
        codes_df = pd.read_pickle(self.codes_path)
        code_col = "symbol" if "symbol" in codes_df.columns else ("code" if "code" in codes_df.columns else "股票代码")
        codes = codes_df[code_col].drop_duplicates().tolist()
        for idx, code in enumerate(codes, 1):
            await self.update_one(code, idx, len(codes))

    async def update_one(self, symbol, idx=1, total=1):
        save_path = os.path.join(self.save_dir, f"{symbol}_daily.pkl")
        if os.path.exists(save_path):
            print(f"[{idx}/{total}] {symbol} 已存在，跳过")
            return
        symbol_full = symbol if symbol.startswith("sh") or symbol.startswith("sz") else f"sz{symbol}"
        df_60min = await self.fetch_60min_data(symbol_full)
        await asyncio.sleep(2)
        df_daily = self.minute_to_daily(df_60min)
        if df_daily is not None and not df_daily.empty:
            df_daily.to_pickle(save_path)
            print(f"[{idx}/{total}] {symbol} 日线数据已保存，{len(df_daily)} 天")
        else:
            print(f"[{idx}/{total}] {symbol} 无有效日线数据")

if __name__ == "__main__":
    fetcher = SinaDailyFetcher()
    # 默认全部
    asyncio.run(fetcher.update_all())
    # # 只更新指定symbol
    # asyncio.run(fetcher.update_one("sz000001"))