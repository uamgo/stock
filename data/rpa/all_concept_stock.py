import os
import pickle
import asyncio
import pandas as pd
from playwright.async_api import async_playwright

BASE_DIR = "/tmp/stock/base"
CONCEPT_MAP_PATH = os.path.join(BASE_DIR, "concept_map.pkl")
SAVE_DIR = os.path.join(BASE_DIR, "concepts")
os.makedirs(SAVE_DIR, exist_ok=True)

async def fetch_concept_stocks(concept_code):
    url = f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=1000&sort=symbol&asc=1&node={concept_code}&symbol=&_s_r_a=init"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        content = await page.content()
        await browser.close()
        # 提取页面中的 json 数据
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

def load_concept_df():
    with open(CONCEPT_MAP_PATH, "rb") as f:
        return pickle.load(f)

async def main():
    concept_df = load_concept_df()
    # 假设DataFrame有“概念代码”和“概念名称”两列
    for _, row in concept_df.iterrows():
        code = row["概念代码"]
        concept_name = row["概念名称"]
        print(f"正在获取概念：{concept_name}（{code}），进度：{_ + 1}/{len(concept_df)}")
        df = await fetch_concept_stocks(code)
        if df is not None and not df.empty:
            save_path = os.path.join(SAVE_DIR, f"{code}.pkl")
            df.to_pickle(save_path)
            print(f"已保存 {concept_name}（{code}）成分股到 {save_path}，共 {len(df)} 只股票")
        else:
            print(f"{concept_name}（{code}）无数据或解析失败")

if __name__ == "__main__":
    asyncio.run(main())