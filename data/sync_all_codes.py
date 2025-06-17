import time
import datetime
import akshare as ak
from mongo_utils import get_mongo_client, with_mongo_transaction

def get_all_stock_codes():
    """获取所有A股股票代码"""
    df = ak.stock_zh_a_spot_em()
    time.sleep(3)
    return df['代码'].tolist()

def is_recent(dt: datetime.datetime, months=1):
    """判断时间是否在一个月内"""
    return (datetime.datetime.now() - dt).days < 30

@with_mongo_transaction
def sync_all_codes(db, session):
    code_col = db['stock_codes']
    code_doc = code_col.find_one({'_id': 'all_codes'}, session=session)
    now = datetime.datetime.now()
    if code_doc and 'update_time' in code_doc and is_recent(code_doc['update_time']):
        codes = code_doc['codes']
        print(f"股票代码已存在且在一个月内，无需更新，数量: {len(codes)}")
    else:
        codes = get_all_stock_codes()
        code_col.update_one(
            {'_id': 'all_codes'},
            {'$set': {'codes': codes, 'update_time': now}},
            upsert=True,
            session=session
        )
        print(f"已更新股票代码，数量: {len(codes)}")
    return codes

if __name__ == "__main__":
    sync_all_codes()