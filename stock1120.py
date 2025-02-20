import datetime
from typing import List

import akshare as ak
import exchange_calendars as xcals


def is_trading_day() -> bool:
  xshg = xcals.get_calendar("XSHG")
  return xshg.is_session(datetime.datetime.now().strftime("%Y-%m-%d"))


def get_top_concept_stocks(top_n: int = 10, date: str = None) -> List[str]:
  concept_df = ak.stock_board_concept_name_em()
  top_concepts = concept_df.head(top_n)
  stocks = [
    stock
    for concept in top_concepts['板块名称']
    for stock in ak.stock_board_concept_cons_em(symbol=concept)['代码'].tolist()
  ]
  return stocks


def filter_stocks(stocks: List[str]) -> List[str]:
  filtered_stocks = []
  for index, stock in enumerate(stocks):
    stock_df = ak.stock_zh_a_hist(
      symbol=stock, period="daily", start_date="20220101", end_date=datetime.datetime.now().strftime("%Y%m%d")
    )
    if len(stock_df) < 26:  # MACD requires at least 26 periods
      continue

    stock_df['EMA12'] = stock_df['收盘'].ewm(span=12, adjust=False).mean()
    stock_df['EMA26'] = stock_df['收盘'].ewm(span=26, adjust=False).mean()
    stock_df['MACD'] = stock_df['EMA12'] - stock_df['EMA26']
    stock_df['Signal'] = stock_df['MACD'].ewm(span=9, adjust=False).mean()
    stock_df['MACD_Hist'] = stock_df['MACD'] - stock_df['Signal']

    # Exclude stocks that have been rising for the last 3 days
    if all(stock_df['收盘'].iloc[-i] > stock_df['收盘'].iloc[-i-1] for i in range(1, 4)):
      continue

    if (
      stock_df['MACD_Hist'].iloc[-1] > stock_df['MACD_Hist'].iloc[-2] > stock_df['MACD_Hist'].iloc[-3]
      and stock_df['MACD_Hist'].iloc[-2] > stock_df['MACD_Hist'].iloc[-3]
    ):
      filtered_stocks.append(stock)
    
    print(f"Processing stock {index + 1}/{len(stocks)}: {stock}")

  return filtered_stocks


def main() -> None:
  if is_trading_day():
    stocks = get_top_concept_stocks()
    filtered_stocks = filter_stocks(stocks)
    print("Filtered Stocks:", filtered_stocks)


if __name__ == "__main__":
  main()