import time
import datetime
import akshare as ak
from mongo_utils import get_mongo_client, with_mongo_transaction
import exchange_calendars as xcals

def is_trade_day(date: datetime.date) -> bool:
    """使用交易日历判断是否为A股交易日"""
    xshg = xcals.get_calendar("XSHG")
    return xshg.is_session(date)

@with_mongo_transaction
def sync_daily_only(db, session):
    # 判断今天是否为交易日
    today = datetime.datetime.now().date()
    if not is_trade_day(today):
        print(f"{today} 不是交易日，不同步。")
        return

    code_col = db['stock_codes']
    hist_col = db['stock_daily_hist']

    # 获取已同步的股票代码
    code_doc = code_col.find_one({'_id': 'all_codes'}, session=session)
    if not code_doc or 'codes' not in code_doc:
        print("请先同步 all_codes！")
        return
    codes = code_doc['codes']

    today_str = today.strftime("%Y-%m-%d")
    for idx, code in enumerate(codes, 1):
        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=today_str, end_date=today_str, adjust="")
            time.sleep(3)
            if df.empty:
                print(f"[{idx}/{len(codes)}] {code} 当日无数据")
                continue
            data = df.to_dict('records')
            hist_col.update_one(
                {'_id': code},
                {'$push': {'data': {'$each': data}}, '$set': {'update_time': datetime.datetime.now()}},
                upsert=True,
                session=session
            )
            print(f"[{idx}/{len(codes)}] {code} 当日日线数据已同步，{len(data)} 条")
        except Exception as e:
            print(f"[{idx}/{len(codes)}] {code} 获取失败: {e}")

if __name__ == "__main__":
    sync_daily_only()