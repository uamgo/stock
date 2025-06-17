import asyncio
from playwright.async_api import async_playwright

STOCK_URL = "https://vip.stock.finance.sina.com.cn/mkt/#stock_hs_up"

async def handle_response(response):
    url = response.url
    if "hq.sinajs.cn" in url and "rn=" in url:
        text = await response.text()
        print(f"Matched response URL: {url}")
        print(text)
        # 提取股票数据
        lines = text.strip().split('\n')
        for line in lines:
            if not line.startswith("var hq_str_"):
                continue
            try:
                code = line.split('=')[0][-6:]
                data = line.split('="')[1].split('",')[0].split(',')
                if len(data) < 10:
                    continue
                stock_info = {
                    "股票代码": code,
                    "股票名称": data[0],
                    "今开": data[1],
                    "昨收": data[2],
                    "最新价": data[3],
                    "最高": data[4],
                    "最低": data[5],
                    "买入": data[6],
                    "卖出": data[7],
                    "成交量": data[8],
                    "成交额": data[9]
                }
                print(stock_info)
            except Exception as e:
                print(f"解析股票数据异常: {e}")

async def fetch_sina_table():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        page = await browser.new_page()
        page.on("response", lambda response: asyncio.create_task(handle_response(response)))

        try:
            await page.goto(STOCK_URL, wait_until="load", timeout=5000)
        except Exception as e:
            print(f"页面加载异常: {e}")

        # 点击“代码”标签，切换到股票代码表格
        try:
            locator = page.locator('#tbl_wrap > table > thead > tr > th:nth-child(1) > a')
            if await locator.count() > 0:
                await locator.first.click()
                print("已点击‘代码’标签")
            else:
                print("未找到‘代码’标签的位置")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"点击‘代码’标签异常: {e}")

        # 点击“每页显示100条”按钮
        try:
            amount_btn = page.locator('#list_amount_ctrl > a:nth-child(3)')
            if await amount_btn.count() > 0:
                await amount_btn.first.click()
                print("已点击‘每页显示100条’按钮")
                await asyncio.sleep(2)
            else:
                print("未找到‘每页显示100条’按钮")
        except Exception as e:
            print(f"点击‘每页显示100条’按钮异常: {e}")

        # 获取总页码数
        total_pages = 1
        try:
            page_links_all = await page.locator('#list_pages_top2').all()
            if page_links_all:
                first_pages = page_links_all[0]
                page_links = await first_pages.locator('a').all_inner_texts()
                page_numbers = [int(text) for text in page_links if text.strip().isdigit()]
                if page_numbers:
                    total_pages = max(page_numbers)
            print(f"总页码数: {total_pages}")
        except Exception as e:
            print(f"获取总页码数异常: {e}")

        # 自动翻页
        try:
            for page_num in range(2, total_pages + 1):
                next_btn = page.locator('#list_pages_top2 a', has_text="下一页")
                if await next_btn.is_enabled():
                    await next_btn.click()
                    await asyncio.sleep(5)
                    print(f"翻到第 {page_num} 页")
                else:
                    print("已到最后一页")
                    break
        except Exception as e:
            print(f"翻页异常: {e}")

        await asyncio.sleep(3)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_sina_table())
