import os
import time
import datetime
import akshare as ak
from mongo_utils import get_mongo_client, with_mongo_transaction
import exchange_calendars as xcals

def is_trade_time():
    """判断当前是否为A股交易时间（9:30-11:30, 13:00-15:00，周一到周五，且为交易日）"""
    now = datetime.datetime.now()
    # 使用 exchange_calendars 判断是否为交易日
    xshg = xcals.get_calendar("XSHG")
    if not xshg.is_session(now.date()):
        return False
    t = now.time()
    return (datetime.time(9, 30) <= t <= datetime.time(11, 30)) or (datetime.time(13, 0) <= t <= datetime.time(15, 0))

@with_mongo_transaction
def sync_minute(db, session):
    minute_col = db['stock_realtime']
    code_doc = db['stock_codes'].find_one({'_id': 'all_codes'}, session=session)
    if not code_doc or 'codes' not in code_doc:
        print("请先同步 all_codes！")
        return
    codes = code_doc['codes']

    while True:
        if is_trade_time():
            try:
                df = ak.stock_zh_a_spot_em()
                now = datetime.datetime.now()
                data = df[df['代码'].isin(codes)].to_dict('records')
                minute_col.insert_one(
                    {
                        'timestamp': now,
                        'data': data
                    },
                    session=session
                )
                print(f"{now} 实时行情已同步，股票数: {len(data)}")
            except Exception as e:
                print(f"{datetime.datetime.now()} 实时行情同步失败: {e}")
        else:
            print(f"{datetime.datetime.now()} 非交易时间，等待中...")
        time.sleep(30)

if __name__ == "__main__":
    sync_minute()