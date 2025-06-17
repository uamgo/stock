import time
import datetime
import akshare as ak
from mongo_utils import get_mongo_client, with_mongo_transaction

SLEEP_SECONDS = 5

def fetch_concept_list():
    """获取所有概念板块列表"""
    df = ak.stock_board_concept_name_em()
    time.sleep(SLEEP_SECONDS)
    return df.to_dict('records')

def fetch_concept_detail(name):
    """获取指定概念板块的成分股明细"""
    df = ak.stock_board_concept_cons_em(name)
    time.sleep(SLEEP_SECONDS)
    return df.to_dict('records')

@with_mongo_transaction
def sync_concept(db, session):
    concept_col = db['concept_board']
    concept_detail_col = db['concept_board_detail']

    # 1. 获取所有概念板块列表
    try:
        concepts = fetch_concept_list()
        concept_col.delete_many({}, session=session)
        concept_col.insert_many(concepts, session=session)
        print(f"已同步概念板块列表，共 {len(concepts)} 个")
    except Exception as e:
        print(f"获取概念板块列表失败: {e}")
        return

    # 2. 获取每个概念板块的成分股明细（已存在则跳过）
    for idx, concept in enumerate(concepts, 1):
        name = concept.get('板块名称')
        code = concept.get('板块代码')
        # 查询是否已存在明细
        exist = concept_detail_col.find_one({'_id': code, 'data.0': {'$exists': True}}, session=session)
        if exist:
            print(f"[{idx}/{len(concepts)}] {name}({code}) 明细已存在，跳过")
            continue
        try:
            detail_data = fetch_concept_detail(name)
            concept_detail_col.update_one(
                {'_id': code},
                {'$set': {
                    'name': name,
                    'code': code,
                    'data': detail_data,
                    'update_time': datetime.datetime.now()
                }},
                upsert=True,
                session=session
            )
            print(f"[{idx}/{len(concepts)}] {name}({code}) 成分股已同步，{len(detail_data)} 条")
        except Exception as e:
            print(f"[{idx}/{len(concepts)}] {name}({code}) 获取失败: {e}")

if __name__ == "__main__":
    sync_concept()