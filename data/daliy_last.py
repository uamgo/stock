import datetime
import logging
import time
from typing import Dict, List
import pandas as pd
from exchange_calendars import get_calendar
import akshare as ak

def get_previous_trading_date() -> str:
    xshg = get_calendar("XSHG")
    today = pd.Timestamp.today().normalize()
    prev = today - pd.Timedelta(days=1)
    while not xshg.is_session(prev):
        prev -= pd.Timedelta(days=1)
    return prev.strftime("%Y%m%d")

def volume_filter(all_data: Dict[str, pd.DataFrame], prev_trade_date: str) -> List[str]:
    result = []
    prev_trade_date_fmt = pd.to_datetime(prev_trade_date).strftime('%Y-%m-%d')
    for code, df in all_data.items():
        df = df.sort_values('日期')
        prev_day_row = df[df['日期'] == prev_trade_date_fmt]
        if prev_day_row.empty:
            continue
        prev_idx = prev_day_row.index[0]
        if prev_idx < 3:
            continue
        window = df.iloc[prev_idx-3:prev_idx+1]
        prev_vol = window.iloc[-1]['成交量']
        max_vol = window.iloc[:-1]['成交量'].max()
        if prev_vol < max_vol * 0.5:
            result.append(code)
    return result

def fetch_all_stock_codes() -> List[str]:
    # TODO: Replace with actual logic to fetch all stock codes
    stock_list = ak.stock_zh_a_spot()
    return stock_list['代码'].tolist()

def filter_stocks(stocks: List[str]) -> List[str]:
    # Dummy implementation, replace with actual logic
    return stocks

def fetch_daily_stock_data(stock_codes: List[str]) -> Dict[str, pd.DataFrame]:
    data = {}
    now = datetime.datetime.now()
    end_date = now.strftime('%Y%m%d')
    start_date = (now - datetime.timedelta(days=20)).strftime('%Y%m%d')
    for code in stock_codes:
        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="")
            data[code] = df
        except Exception as e:
            logging.warning(f"Failed to fetch data for {code}: {e}")
    return data

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("当前程序用于尾盘选股")
    prev_trade_date = get_previous_trading_date()
    start_time = time.perf_counter()
    try:
        all_stocks = fetch_all_stock_codes()
        logging.info(f"Number of stocks fetched: {len(all_stocks)}")
        filtered_codes = filter_stocks(all_stocks)
        stock_data = fetch_daily_stock_data(filtered_codes)
        filtered_stocks = volume_filter(stock_data, prev_trade_date)
        logging.info(f"Filtered stocks: {len(filtered_stocks)}")
        with open('/Users/kevin/Downloads/filtered_stocks_last.txt', 'w') as f:
            f.write(','.join(filtered_stocks))
    except Exception as e:
        logging.exception("Error in fetching all stocks")
    total_time = time.perf_counter() - start_time
    logging.info(f"Total time taken: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
