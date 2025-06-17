import os
from pymongo import MongoClient

def get_mongo_client():
    """
    获取MongoDB数据库连接，返回数据库对象（默认数据库为stock）。
    """
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://uamgo:uamgo!pro!021@code.uamgo.com:27017/admin')
    return MongoClient(mongo_uri)['stock']

def get_collection(col_name: str):
    """
    获取指定集合对象
    """
    db = get_mongo_client()
    return db[col_name]

def with_mongo_transaction(func):
    """
    装饰器：自动开启并提交MongoDB事务（如环境支持）。
    被装饰的函数需接收db和session两个参数。
    """
    def wrapper(*args, **kwargs):
        db = get_mongo_client()
        client = db.client
        # 判断是否支持事务
        is_replica_set = False
        try:
            is_replica_set = client.is_mongos or client.topology_description.topology_type_name == "ReplicaSetWithPrimary"
        except Exception:
            pass
        if is_replica_set:
            with client.start_session() as session:
                with session.start_transaction():
                    result = func(db, session, *args, **kwargs)
                    session.commit_transaction()
                    return result
        else:
            # 不支持事务，session 传 None
            return func(db, None, *args, **kwargs)
    return wrapper