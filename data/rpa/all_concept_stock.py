import os
import pickle
import asyncio
import pandas as pd
from playwright.async_api import async_playwright

class ConceptStockFetcher:
    def __init__(self, base_dir="/tmp/stock/base"):
        self.base_dir = base_dir
        self.concept_map_path = os.path.join(self.base_dir, "concept_map.pkl")
        self.save_dir = os.path.join(self.base_dir, "concepts")
        os.makedirs(self.save_dir, exist_ok=True)

    async def fetch_concept_stocks(self, concept_code):
        url = f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=1000&sort=symbol&asc=1&node={concept_code}&symbol=&_s_r_a=init"
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
                df = pd.read_json(json_str)
                return df
            except Exception as e:
                print(f"{concept_code} 解析失败: {e}")
                return None

    def load_concept_df(self):
        with open(self.concept_map_path, "rb") as f:
            return pickle.load(f)

    async def update_concept_stocks(self, top_n=None, force_update=False):
        concept_df = self.load_concept_df()
        # 排序并筛选涨幅前 top_n 的概念（如果指定）
        if top_n is not None and "涨跌幅" in concept_df.columns:
            concept_df = concept_df.sort_values(by="涨跌幅", ascending=False).head(top_n)
            print(f"只更新涨幅排名前 {top_n} 的概念股")
        else:
            print("更新全部概念股")
        for idx, row in concept_df.iterrows():
            code = row["概念代码"]
            concept_name = row["概念名称"]
            save_path = os.path.join(self.save_dir, f"{code}.pkl")
            if not force_update and os.path.exists(save_path):
                print(f"已存在 {save_path}，跳过")
                continue
            print(f"正在获取概念：{concept_name}（{code}），进度：{idx + 1}/{len(concept_df)}")
            df = await self.fetch_concept_stocks(code)
            if df is not None and not df.empty:
                df.to_pickle(save_path)
                print(f"已保存 {concept_name}（{code}）成分股到 {save_path}，共 {len(df)} 只股票")
            else:
                print(f"{concept_name}（{code}）无数据或解析失败")

if __name__ == "__main__":
    fetcher = ConceptStockFetcher()
    # 默认全部，不强制更新
    # asyncio.run(fetcher.update_concept_stocks())
    # # 只更新涨幅前30的概念股，强制更新
    asyncio.run(fetcher.update_concept_stocks(top_n=30, force_update=False))