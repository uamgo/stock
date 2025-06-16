import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

# 初始化 tushare
ts.set_token('262fbed211d1fb85130e2a76d588a1211dd1c552a88ea9a61f8ce251')
pro = ts.pro_api()

# 1. 获取最近一个交易日排名前30的概念及其股票
today = datetime.today().strftime('%Y%m%d')
trade_cal = pro.trade_cal(exchange='', start_date=(datetime.today()-timedelta(days=10)).strftime('%Y%m%d'), end_date=today)
trade_days = trade_cal[trade_cal['is_open'] == 1]['cal_date'].tolist()
last_trade_day = trade_days[-1]

# 获取概念板块排名前30
concepts = pro.concept(src='ts')
concepts_top30 = concepts.head(30)

# 获取每个概念下的股票
stocks = set()
for code in concepts_top30['code']:
    df = pro.concept_detail(id=code)
    stocks.update(df['ts_code'].tolist())

# 2. 留下最近5个交易日内个股交易量在5日平均以下的股票
selected_stocks = []
for ts_code in stocks:
    df = pro.daily(ts_code=ts_code, start_date=trade_days[-5], end_date=last_trade_day)
    if len(df) < 5:
        continue
    vol_5avg = df['vol'].mean()
    if df.iloc[0]['vol'] < vol_5avg:
        selected_stocks.append(ts_code)

# 3. MACD在水下的股票
final_stocks = []
for ts_code in selected_stocks:
    df = pro.daily(ts_code=ts_code, start_date=trade_days[-60], end_date=last_trade_day)
    if len(df) < 26:
        continue
    close = df.sort_values('trade_date')['close']
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9).mean()
    macd = dif - dea
    if macd.iloc[-1] < 0:
        final_stocks.append(ts_code)

print("最终筛选股票：", final_stocks)