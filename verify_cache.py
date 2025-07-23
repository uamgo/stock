#!/usr/bin/env python3
import asyncio
from data.est.req.est_prepare_data import EstStockPipeline

async def verify_cache():
    pipeline = EstStockPipeline(top_n=3)
    print('🔄 验证缓存机制 (应该使用缓存):')
    codes = await pipeline.get_top_n_concepts()
    print(f'TOP3代码: {codes}')

if __name__ == "__main__":
    asyncio.run(verify_cache())
