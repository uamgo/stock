import re
import json
import requests
from playwright.async_api import async_playwright

async def fetch_all_pages(page_obj, base_url):
    """
    循环分页抓取所有数据，返回所有行和总数
    :param page_obj: playwright page对象
    :param base_url: 带有 {page} 占位符的url
    :return: (all_rows, total)
    """
    all_rows = []
    total = None
    page = 1
    while True:
        url = base_url.format(page=page)
        try:
            await page_obj.goto(url, timeout=10000)  # 10秒超时
            await page_obj.wait_for_load_state('networkidle')
            content = await page_obj.content()
        except Exception as e:
            print(f"页面跳转异常: {e}")
            break

        match = re.search(r'json\((\{.*?\})\)', content, re.DOTALL)
        if not match:
            print("未找到有效数据")
            break

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            break

        page_data = data.get("data", {})
        if total is None:
            total = page_data.get("total", 0)
        rows = page_data.get("diff", [])
        if not rows:
            break
        all_rows.extend(rows)
        print(f"当前已获取行数: {len(all_rows)}, 总数: {total}")
        if len(all_rows) >= total:
            break
        page += 1
    return all_rows, total

def get_kuai_proxy():
    url = (
        "https://dps.kdlapi.com/api/getdps/"
        "?secret_id=oclh0ypvdwf4q2fkui5i"
        "&signature=m94dxnhkd5zhcryjyv94lc5z7y54p4np"
        "&num=1&format=text&sep=%2C&dedup=1"
    )
    username = "d4198818119"
    password = "4rhkjwk2"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        proxy_addr = resp.text.strip()
        # 返回属性列表，包含代理、用户名、密码
        return {
            "proxy": proxy_addr,
            "username": username,
            "password": password
        }
    except requests.RequestException as e:
        print(f"获取代理失败: {e}")
        return None
    
def get_proxy():
    return get_kuai_proxy()

async def init_async_playwright():
    playwright = await async_playwright().start()
    return playwright

async def close_async_playwright(playwright):
    await playwright.stop()