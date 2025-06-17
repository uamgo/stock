import asyncio
import re
import json
from playwright.async_api import async_playwright
import pandas as pd
import os

async def fetch_sina_concept_map():
    url = "https://money.finance.sina.com.cn/q/view/newFLJK.php?param=class"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        content = await page.content()
        await browser.close()

        # 直接用 split 提取 JSON 部分
        parts = re.split(r'=\s*', content, maxsplit=1)
        if len(parts) < 2:
            print("未找到概念板块数据")
            return None
        # 解析为 dict
        # parts[1] 可能包含多余的分号和换行，需要提取大括号内的内容
        match = re.search(r'\{.*\}', parts[1], re.DOTALL)
        if not match:
            print("未找到有效的概念板块 JSON")
            return None
        json_str = match.group(0)
        concept_map = json.loads(json_str)
        return concept_map

if __name__ == "__main__":
    concept_map = asyncio.run(fetch_sina_concept_map())
    if concept_map:
        data = []
        for v in concept_map.values():
            fields = v.strip().split(',')
            if len(fields) >= 13:
                data.append({
                    "概念代码": fields[0],
                    "概念名称": fields[1],
                    "公司家数": fields[2],
                    "平均价格": fields[3],
                    "涨跌额": fields[4],
                    "涨跌幅": fields[5],
                    "总成交量(手)": fields[6],
                    "总成交额(万元)": fields[7],
                    "领涨股": fields[8],
                    "领涨股当前价": fields[9],
                    "领涨股涨跌幅": fields[10],
                    "领涨股涨跌额": fields[11],
                    "领涨股名称": fields[12]
                })
        df = pd.DataFrame(data)
        df["涨跌幅"] = pd.to_numeric(df["涨跌幅"], errors="coerce")
        df = df.sort_values(by="涨跌幅", ascending=False)
        print(df)
        output_dir = "/tmp/stock/base"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "concept_map.pkl")
        df.to_pickle(output_path)
        print(f"已保存到 {output_path}")
