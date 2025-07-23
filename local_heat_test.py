#!/usr/bin/env python3
"""
本地环境热度对比测试
对比不同时间点的热度计算结果
"""

import os
import asyncio
from datetime import datetime

async def test_local_heat_comparison():
    """测试本地环境不同时间的热度变化"""
    print("🔍 本地环境热度对比测试")
    print(f"📍 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        from data.est.req.est_prepare_data import EstStockPipeline
        from data.est.req.est_concept import EastmoneyConceptStockFetcher
        
        # 创建pipeline
        pipeline = EstStockPipeline(top_n=10)
        
        # 第一次测试：使用缓存数据
        print("\n🔄 第一次测试：使用缓存数据")
        top_codes_cached = await pipeline.get_top_n_concepts()
        
        # 第二次测试：强制刷新数据
        print("\n🔄 第二次测试：强制刷新数据")
        
        # 清除缓存
        cache_path = pipeline.cache_dir / "top_concepts.pkl"
        concept_cache = "/tmp/stock/base/eastmoney_concept_stocks.pkl"
        
        if cache_path.exists():
            os.remove(cache_path)
            print("🗑️ 已清除热度缓存")
            
        if os.path.exists(concept_cache):
            os.remove(concept_cache)
            print("🗑️ 已清除概念数据缓存")
        
        # 重新获取
        top_codes_fresh = await pipeline.get_top_n_concepts()
        
        # 对比结果
        print("\n📊 对比结果:")
        print(f"缓存版本TOP5代码: {top_codes_cached[:5]}")
        print(f"最新版本TOP5代码: {top_codes_fresh[:5]}")
        
        if top_codes_cached[:5] == top_codes_fresh[:5]:
            print("✅ 两次结果一致")
        else:
            print("⚠️ 两次结果不同，说明数据发生了变化")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_local_heat_comparison())
