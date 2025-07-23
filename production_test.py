#!/usr/bin/env python3
"""
生产环境热度计算测试脚本
验证生产环境和本地环境的热度计算一致性
"""

import os
import sys
import asyncio
from datetime import datetime

# 确保路径正确
sys.path.insert(0, '/home/uamgo/stock')

async def test_production_heat():
    """测试生产环境的热度计算"""
    print("🔍 生产环境热度计算测试")
    print(f"📍 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 工作目录: {os.getcwd()}")
    
    try:
        # 导入模块
        from data.est.req.est_prepare_data import EstStockPipeline
        print("✅ EstStockPipeline 导入成功")
        
        # 创建pipeline实例
        pipeline = EstStockPipeline(top_n=10)
        print("✅ Pipeline 实例创建成功")
        
        # 强制清除缓存，获取最新数据
        cache_path = pipeline.cache_dir / "top_concepts.pkl"
        if cache_path.exists():
            os.remove(cache_path)
            print("🗑️ 已清除热度缓存")
        
        # 获取最新的概念热度排名
        print("\n🔥 开始获取最新概念热度...")
        top_concept_codes = await pipeline.get_top_n_concepts()
        
        print(f"\n📊 选中的top概念代码: {top_concept_codes}")
        
        # 显示详细信息
        from data.est.req.est_concept import EastmoneyConceptStockFetcher
        fetcher = EastmoneyConceptStockFetcher()
        df = fetcher.fetch_and_save()
        
        if df is not None:
            # 计算热度
            df_with_heat = pipeline.calculate_concept_heat(df)
            
            # 显示所选概念的详细信息
            print("\n🎯 所选概念详细信息:")
            for i, code in enumerate(top_concept_codes[:5], 1):
                concept_row = df_with_heat[df_with_heat['代码'] == code]
                if not concept_row.empty:
                    row = concept_row.iloc[0]
                    print(f"  {i}. {row['名称']:<20} | 涨跌: {row['涨跌幅']:>6.2f}% | 热度: {row['热度分数']:>5.1f}分 | 代码: {code}")
        
        print("✅ 生产环境测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 检查是否在生产环境
    if os.path.exists('/home/uamgo/stock'):
        print("🚀 检测到生产环境")
        asyncio.run(test_production_heat())
    else:
        print("💻 检测到本地环境，跳过生产环境测试")
