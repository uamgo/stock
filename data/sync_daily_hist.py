import time
import datetime
import akshare as ak
from mongo_utils import get_mongo_client, with_mongo_transaction
import exchange_calendars as xcals

def get_recent_trade_dates(n=7):
    """获取最近n个A股交易日（含今天，倒序）"""
    xshg = xcals.get_calendar("XSHG")
    today = datetime.datetime.now().date()
    sessions = xshg.sessions_in_range(today - datetime.timedelta(days=30), today)
    trade_dates = [d.date() for d in sessions][-n:]
    return [d.strftime("%Y-%m-%d") for d in trade_dates]

@with_mongo_transaction
def sync_daily_hist(db, session):
    code_col = db['stock_codes']
    hist_col = db['stock_daily_hist']

    # 获取已同步的股票代码
    code_doc = code_col.find_one({'_id': 'all_codes'}, session=session)
    if not code_doc or 'codes' not in code_doc:
        print("请先同步 all_codes！")
        return
    codes = code_doc['codes']

    # 获取最近7个交易日
    recent_dates = get_recent_trade_dates(7)
    start_date, end_date = recent_dates[0], recent_dates[-1]

    # 判断今天是否为交易日
    xshg = xcals.get_calendar("XSHG")
    today = datetime.datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")
    is_today_trade = xshg.is_session(today)
    check_date = today_str if is_today_trade else recent_dates[-1]

    loop_start_time = time.time()
    for idx, code in enumerate(codes, 1):
        # 查询MongoDB中该股票的日线数据
        doc = hist_col.find_one({'_id': code}, {'data.日期': 1, 'data.date': 1}, session=session)
        date_set = set()
        if doc and 'data' in doc:
            for record in doc['data']:
                date_val = record.get('日期') or record.get('date')
                if date_val:
                    date_set.add(date_val)
        if check_date in date_set:
            print(f"[{idx}/{len(codes)}] {code} 已有{check_date}数据，跳过")
            continue

        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="")
            time.sleep(2)
            data = df.to_dict('records')
            # Convert all datetime.date objects to string for MongoDB compatibility
            for record in data:
                for k, v in record.items():
                    if isinstance(v, (datetime.date, datetime.datetime)):
                        record[k] = v.strftime("%Y-%m-%d")
            hist_col.update_one(
                {'_id': code},
                {'$set': {'data': data, 'update_time': datetime.datetime.now()}},
                upsert=True,
                session=session
            )
            elapsed = time.time() - loop_start_time
            print(f"[{elapsed:.2f}s] [{idx}/{len(codes)}] {code} 近7日数据已更新，{len(data)} 条")
        except Exception as e:
            print(f"[{idx}/{len(codes)}] {code} 获取失败: {e}")

if __name__ == "__main__":
    sync_daily_hist()
