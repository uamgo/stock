import akshare as ak
import datetime
from typing import List, Dict, Optional
import pandas as pd
import exchange_calendars as xcals
import logging
import time
import math
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

NAME_BLACK_PREFIXES = ['*ST', 'ST', '退市', 'N', 'L', 'C', 'U', 'bj', 'BJ']
CODE_BLACK_LIST = ['8', '688']

def get_previous_trading_date() -> str:
    xshg = xcals.get_calendar("XSHG")
    today = pd.Timestamp(datetime.datetime.now().strftime("%Y-%m-%d"))
    prev = today - pd.Timedelta(days=1)
    while not xshg.is_session(prev):
        prev -= pd.Timedelta(days=1)
    return prev.strftime("%Y%m%d")

def fetch_top_concept_stocks(top_n: int = 10) -> List[Dict[str, str]]:
    concept_df = pd.read_pickle("/tmp/stock/base/concept_map.pkl")
    top_concepts = concept_df.sort_values('涨跌幅', ascending=False).head(top_n)['概念代码']
    stocks = []
    concept_dir = Path("/tmp/stock/base/concepts")
    for concept_code in top_concepts:
        concept_file = concept_dir / f"{concept_code}.pkl"
        if concept_file.exists():
            df = pd.read_pickle(concept_file)
            stocks.append(df)
    if stocks:
        all_stocks_df = pd.concat(stocks, ignore_index=True)
        all_stocks_df = all_stocks_df.drop_duplicates(subset=['symbol'])
        return all_stocks_df.to_dict(orient='records')
    return []

def filter_stocks(stocks: List[Dict[str, str]]) -> List[str]:
    return [
        s['symbol'] for s in stocks
        if not any(s['symbol'].startswith(prefix) for prefix in NAME_BLACK_PREFIXES)
        and not any(s['symbol'].startswith(code) for code in CODE_BLACK_LIST)
    ]

def get_black_list_path() -> Path:
    today_str = datetime.datetime.now().strftime('%Y%m%d')
    black_list_dir = Path(f"/tmp/{today_str}")
    black_list_dir.mkdir(parents=True, exist_ok=True)
    return black_list_dir / "black_list.txt"

def load_black_list() -> List[str]:
    path = get_black_list_path()
    if path.exists():
        content = path.read_text().strip()
        if content:
            return content.split(',')
    return []

def save_black_list(black_list: List[str]):
    path = get_black_list_path()
    path.write_text(','.join(black_list))

def fetch_daily_stock_data(
    stock_list: List[str],
    black_list: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    if start_date is None:
        start_date = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime("%Y%m%d")
    if end_date is None:
        end_date = datetime.datetime.now().strftime("%Y%m%d")
    stock_data = {}
    data_dir = Path("/tmp/stock/base/daily")
    data_dir.mkdir(parents=True, exist_ok=True)
    total = len(stock_list)
    for idx, code in enumerate(stock_list, 1):
        if code in black_list:
            continue
        try:
            file_path = data_dir / f"{code}.df"
            if file_path.exists():
                df = pd.read_pickle(file_path)
            else:
                df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="")
                df.to_pickle(file_path)
                time.sleep(1.5)
            df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
            df['股票代码'] = code
            stock_data[code] = df
            logging.info(f"Processed {idx}/{total}: {code}")
        except Exception as e:
            logging.warning(f"Error fetching data for {code}: {e}", exc_info=True)
            time.sleep(1)
            break
    return stock_data

def get_trading_time_ratio(now: datetime.datetime) -> float:
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    lunch_start = now.replace(hour=11, minute=30, second=0, microsecond=0)
    lunch_end = now.replace(hour=13, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=0, second=0, microsecond=0)
    total_trading_minutes = (lunch_start - market_open).seconds // 60 + (market_close - lunch_end).seconds // 60
    if now < market_open:
        passed_minutes = 0
    elif now < lunch_start:
        passed_minutes = (now - market_open).seconds // 60
    elif now < lunch_end:
        passed_minutes = (lunch_start - market_open).seconds // 60
    elif now < market_close:
        passed_minutes = (lunch_start - market_open).seconds // 60 + (now - lunch_end).seconds // 60
    else:
        passed_minutes = total_trading_minutes
    return passed_minutes / total_trading_minutes if total_trading_minutes else 0

def macd_filter(all_data: Dict[str, pd.DataFrame], black_list: List[str]) -> List[str]:
    result = []
    now = datetime.datetime.now()
    trading_time_ratio = get_trading_time_ratio(now)
    today_str = now.strftime('%Y-%m-%d')
    for df in all_data.values():
        recent = df.tail(10)
        today_row = recent[recent['日期'] == today_str]
        today_volume = today_row['成交量'].iloc[0] if not today_row.empty else None
        last_2_days = recent[recent['日期'] < today_str].tail(2)
        if not last_2_days.empty and today_volume is not None:
            max_vol = last_2_days['成交量'].max()
            threshold = math.ceil(max_vol * trading_time_ratio * 0.5)
            code = df['股票代码'].iloc[0]
            if today_volume < threshold:
                result.append(code)
            else:
                if code not in black_list:
                    black_list.append(code)
    return result

def remove_blacklisted_stocks(stocks: List[Dict[str, str]], black_list: List[str]) -> List[Dict[str, str]]:
    if not black_list:
        return stocks
    filtered_stocks = [s for s in stocks if s['代码'] not in black_list]
    logging.info(f"Removed {len(stocks) - len(filtered_stocks)} blacklisted stocks")
    return filtered_stocks

def main():
    logging.info("当前程序用于尾盘选股，适合交易日下午 14:00 之后使用")
    xshg = xcals.get_calendar("XSHG")
    today = pd.Timestamp(datetime.datetime.now().strftime("%Y-%m-%d"))
    next_trading_day = today
    while not xshg.is_session(next_trading_day):
        next_trading_day += pd.Timedelta(days=1)
    if not xshg.is_session(today):
        logging.warning(f"今日不是交易日，程序不可用。下一个交易日为: {next_trading_day.strftime('%Y-%m-%d')}")
        return
    now = datetime.datetime.now()
    allowed_start = now.replace(hour=14, minute=20, second=0, microsecond=0)
    allowed_end = now.replace(hour=14, minute=59, second=59, microsecond=999999)
    # if not (allowed_start <= now <= allowed_end):
    #     logging.warning("程序仅可在交易日下午 14:20 - 14:59 之间运行。")
    #     return
    start_time = time.perf_counter()
    black_list = load_black_list()
    all_stocks = fetch_top_concept_stocks(20)
    all_stocks = remove_blacklisted_stocks(all_stocks, black_list)
    filtered_codes = filter_stocks(all_stocks)
    stock_data = fetch_daily_stock_data(filtered_codes, black_list)
    filtered_stocks = macd_filter(stock_data, black_list)
    Path('/Users/kevin/Downloads/filtered_stocks.txt').write_text(','.join(filtered_stocks))
    save_black_list(black_list)
    logging.info(f"剩余过滤出来的股票数量: {len(filtered_stocks)}")
    logging.info(f"Total time taken: {time.perf_counter() - start_time:.2f}s")

if __name__ == "__main__":
    main()
