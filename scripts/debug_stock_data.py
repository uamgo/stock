#!/usr/bin/env python3
"""
调试股票数据获取问题
"""

import sys
import pandas as pd
sys.path.append('/Users/kevin/workspace/stock')

def debug_stock_data():
    print("=== 股票数据获取调试 ===")
    
    # 1. 直接读取pickle文件
    print("\n1. 直接读取pickle文件:")
    try:
        df = pd.read_pickle('/tmp/stock/est_prepare_data/members_df.pkl')
        print(f"   股票数量: {len(df)}")
        print(f"   列名: {list(df.columns)}")
        if len(df) > 0:
            print("   前5行:")
            print(df.head())
    except Exception as e:
        print(f"   读取失败: {e}")
    
    # 2. 通过 est_prepare_data 模块读取
    print("\n2. 通过 est_prepare_data 模块:")
    try:
        from data.est.req.est_prepare_data import load_members_df_from_path
        df2 = load_members_df_from_path()
        if df2 is not None and not df2.empty:
            print(f"   股票数量: {len(df2)}")
            print(f"   列名: {list(df2.columns)}")
        else:
            print("   没有数据")
    except Exception as e:
        print(f"   读取失败: {e}")
    
    # 3. 通过 EastmoneyDataFetcher 读取
    print("\n3. 通过 EastmoneyDataFetcher:")
    try:
        from tail_trading.data.eastmoney.daily_fetcher import EastmoneyDataFetcher
        fetcher = EastmoneyDataFetcher()
        df3 = fetcher.get_stock_list()
        if df3 is not None and not df3.empty:
            print(f"   股票数量: {len(df3)}")
            print(f"   列名: {list(df3.columns)}")
        else:
            print("   没有数据")
    except Exception as e:
        print(f"   读取失败: {e}")
    
    # 4. 检查缓存
    print("\n4. 检查缓存:")
    try:
        from tail_trading.data.eastmoney.daily_fetcher import EastmoneyDataFetcher
        fetcher = EastmoneyDataFetcher()
        cache_key = "stock_list"
        cached_data = fetcher.get_from_cache(cache_key, expire_minutes=60)
        if cached_data is not None:
            print(f"   缓存数据股票数量: {len(cached_data)}")
        else:
            print("   没有缓存数据")
    except Exception as e:
        print(f"   检查缓存失败: {e}")

if __name__ == "__main__":
    debug_stock_data()
