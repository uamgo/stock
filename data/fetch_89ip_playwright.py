import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

async def fetch_89ip_proxies(max_pages=10):
    proxies = []
    base_url = "https://www.89ip.cn"
    print(f"Fetching proxies from {base_url}, pages: {max_pages}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for page_num in range(1, max_pages + 1):
            url = base_url if page_num == 1 else f"{base_url}/index_{page_num}.html"
            print(f"Page {page_num}: {url}")
            await page.goto(url)
            await page.wait_for_selector('table.layui-table')
            rows = await page.query_selector_all('table.layui-table tbody tr')
            for row in rows:
                tds = await row.query_selector_all('td')
                if len(tds) >= 2:
                    ip = (await tds[0].inner_text()).strip()
                    port = (await tds[1].inner_text()).strip()
                    proxies.append((ip, port))
            await asyncio.sleep(0.3)  # 更优雅的等待
        await browser.close()
    print(f"Fetched {len(proxies)} proxies")
    return proxies

def save_proxies(proxies, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        for ip, port in proxies:
            f.write(f"{ip}:{port}\n")
    print(f"Saved to {file_path}")

def test_proxy(ip, port, timeout=5):
    try:
        with socket.create_connection((ip, int(port)), timeout=timeout):
            return True
    except Exception:
        return False

def filter_proxies_concurrent(proxies, max_workers=10):
    ok, failed = [], []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {executor.submit(test_proxy, ip, port): (ip, port) for ip, port in proxies}
        for i, future in enumerate(as_completed(future_to_proxy), 1):
            ip, port = future_to_proxy[future]
            try:
                if future.result():
                    ok.append((ip, port))
                else:
                    failed.append((ip, port))
            except Exception:
                failed.append((ip, port))
            print(f"Tested {i}/{len(proxies)} proxies... Ok: {len(ok)}, Failed: {len(failed)}", end='\r')
    print()  # 换行
    return ok, failed

def main():
    proxies = asyncio.run(fetch_89ip_proxies(max_pages=100))
    date_str = datetime.now().strftime("%Y-%m-%d")
    base_dir = f"/tmp/proxies/{date_str}"
    if os.path.exists(base_dir):
        for f in os.listdir(base_dir):
            os.remove(os.path.join(base_dir, f))
    else:
        os.makedirs(base_dir, exist_ok=True)
    all_file = f"{base_dir}/89ip_proxies.txt"
    ok_file = f"{base_dir}/89ip_proxies_ok.txt"
    failed_file = f"{base_dir}/89ip_proxies_failed.txt"

    save_proxies(proxies, all_file)
    ok, failed = filter_proxies_concurrent(proxies, max_workers=10)
    save_proxies(ok, ok_file)
    save_proxies(failed, failed_file)
    print(f"Ok: {len(ok)}, Failed: {len(failed)}")

if __name__ == "__main__":
    main()
