import re
import json
import requests
import os
import datetime
import pandas as pd
import exchange_calendars as xcals

def fetch_all_pages(base_url, proxies=None):
    """
    循环分页抓取所有数据，返回所有行和总数（requests 方式）
    :param base_url: 带有 {page} 占位符的url
    :param proxies: requests 支持的 proxies 参数（可选）
    :return: (all_rows, total)
    """
    all_rows = []
    total = None
    page = 1
    while True:
        url = base_url.format(page=page)
        retry = 0
        max_retry = 3
        while retry < max_retry:
            try:
                resp = requests.get(url, timeout=10, proxies=proxies)
                resp.encoding = "utf-8"
                text = resp.text
                break
            except Exception as e:
                print(f"页面请求异常: {e}，尝试更换代理（第{retry+1}次）")
                proxies = get_proxy()
                retry += 1
        else:
            print("连续三次更换代理均失败，终止请求")
            return all_rows, total

        match = re.search(r'json\((\{.*?\})\)', text, re.DOTALL)
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
            "proxy": f"http://{proxy_addr}",
            "username": username,
            "password": password
        }
    except requests.RequestException as e:
        print(f"获取代理失败: {e}")
        return None
    
def get_proxy():
    """
    返回 requests 支持的 http://user:pass@host:port 形式的代理字符串
    """
    proxy_info = get_kuai_proxy()
    if not proxy_info:
        return None
    proxy_addr = proxy_info["proxy"].replace("http://", "")
    user = proxy_info["username"]
    pwd = proxy_info["password"]
    server = proxy_addr
    proxy = {
        "http": f"http://{user}:{pwd}@{server}",
        "https": f"http://{user}:{pwd}@{server}",
    }
    print(f"使用代理: {proxy}")
    return proxy

def need_update(filepath):
    """
    判断文件是否需要更新
    :param filepath: 文件路径
    :return: True 需要更新, False 不需要
    """
    if not os.path.exists(filepath):
        return True

    # 获取文件最后修改时间
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
    now = datetime.datetime.now()
    today = now.date()

    # 判断是否交易日
    try:
        is_trading_day = pd.Timestamp(today) in pd.bdate_range(today, today)
    except Exception:
        is_trading_day = True  # 若pandas不可用，默认是交易日

    if not is_trading_day:
        # 非交易日，且文件不是今天更新的，需要更新
        return mtime.date() != today

    # 交易时间段
    morning_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
    morning_end = now.replace(hour=11, minute=30, second=0, microsecond=0)
    noon_start = now.replace(hour=11, minute=30, second=0, microsecond=0)
    noon_end = now.replace(hour=13, minute=0, second=0, microsecond=0)
    afternoon_start = now.replace(hour=13, minute=0, second=0, microsecond=0)
    afternoon_end = now.replace(hour=15, minute=0, second=0, microsecond=0)

    # 1. 交易日且当前在交易时间内，需更新
    if morning_start <= now <= morning_end or afternoon_start <= now <= afternoon_end:
        return True

    # 2. 交易日且文件不是今天更新的，需更新
    if mtime.date() != today:
        return True

    # 3. 交易日且当前在 11:30-13:00，且文件最后修改时间不在此区间，需更新
    if noon_start <= now <= noon_end:
        if not (noon_start <= mtime <= noon_end):
            return True

    # 4. 交易日且当前在 15:00 之后，且文件最后修改时间不在此区间，需更新
    if now > afternoon_end:
        if not (afternoon_end <= mtime <= now):
            return True

    return False

def need_update_simple(filepath):
    """
    如果文件不存在或不是今天修改的，返回True（需要更新），否则返回False
    """
    if not os.path.exists(filepath):
        return True
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
    today = datetime.datetime.now().date()
    return mtime.date() != today

def save_df_to_file(df: pd.DataFrame, filename: str):
    """
    将 DataFrame 保存到指定文件（csv 格式）
    :param filename: 文件名
    :param df: 要保存的 DataFrame
    """
    df.to_pickle(filename)

def load_df_from_file(filename: str) -> pd.DataFrame:
    """
    从指定文件（pkl 格式）恢复 DataFrame
    :param filename: 文件名
    :return: 恢复的 DataFrame
    """
    if not os.path.exists(filename):
        print(f"文件不存在: {filename}")
        return pd.DataFrame()
    return pd.read_pickle(filename)

def save_codes_to_file(filename: str, codes: list, merge: bool = False):
    """
    将股票代码列表以逗号分隔存入文件
    :param filename: 文件名
    :param codes: 股票代码列表
    :param merge: 是否与文件中已有的股票代码合并后再写入
    """
    codes_set = set(map(str, codes))
    if merge and os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing = f.read().strip()
            if existing:
                codes_set.update(existing.split(","))
    with open(filename, "w", encoding="utf-8") as f:
        f.write(",".join(sorted(codes_set)))

def load_codes_from_file(filename: str) -> list:
    """
    从文件读取逗号分隔的股票代码列表
    :param filename: 文件名
    :return: 股票代码列表
    """
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return content.split(",")
    
def is_trading_day():
    """
    判断今天是否为交易日（上交所），依赖 exchange_calendars
    :return: True/False
    """
    try:
        cal = xcals.get_calendar("XSHG")
        today = pd.Timestamp(datetime.datetime.now().date())
        return cal.is_session(today)
    except Exception as e:
        # 如果无法判断，默认周一到周五为交易日
        today = datetime.datetime.now().weekday()
        return today < 5

