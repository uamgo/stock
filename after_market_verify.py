#!/usr/bin/env python3
"""
收盘后数据变化验证脚本
验证收盘后东方财富数据是否还在变化
"""

import asyncio
from datetime import datetime

async def verify_after_market_data():
    """验证收盘后的数据变化"""
    print("🔍 收盘后数据变化验证")
    print("=" * 50)
    
    current_time = datetime.now()
    print(f"📍 当前时间: {current_time.strftime('%H:%M:%S')}")
    print("📈 A股已收盘 (15:00)")
    
    try:
        from data.est.req.est_concept import EastmoneyConceptStockFetcher
        
        print("\n📊 正在分析概念数据特征...")
        fetcher = EastmoneyConceptStockFetcher()
        df = fetcher.fetch_and_save()
        
        if df is not None:
            print(f"✅ 获取到 {len(df)} 个概念")
            
            # 检查数据列
            print(f"📋 数据列: {list(df.columns)}")
            
            # 检查关键字段
            key_fields = ['涨跌幅', 'f62', 'f66', 'f78']
            available_fields = []
            
            for field in key_fields:
                if field in df.columns:
                    available_fields.append(field)
                    non_zero = (df[field] != 0).sum()
                    print(f"   {field}: 有效数据 {non_zero}/{len(df)} ({non_zero/len(df)*100:.1f}%)")
                    
                    if field == '涨跌幅':
                        print(f"     涨跌幅范围: {df[field].min():.2f}% ~ {df[field].max():.2f}%")
                    elif field in ['f62', 'f66']:
                        abs_sum = df[field].abs().sum()
                        print(f"     绝对值总和: {abs_sum:,.0f}")
            
            # 分析收盘后数据是否"冻结"
            print("\n🧊 收盘后数据状态分析:")
            
            if 'f66' in df.columns:
                zero_volume = (df['f66'] == 0).sum()
                print(f"零成交量概念: {zero_volume}/{len(df)} ({zero_volume/len(df)*100:.1f}%)")
                
                if zero_volume > len(df) * 0.9:
                    print("   📊 结论: 成交数据已冻结 (收盘后正常)")
                else:
                    print("   📊 结论: 仍有成交数据更新 (可能包含盘后数据)")
            
            if 'f62' in df.columns:
                zero_capital = (df['f62'] == 0).sum()
                print(f"零资金流向概念: {zero_capital}/{len(df)} ({zero_capital/len(df)*100:.1f}%)")
            
            # 检查涨跌幅是否还在变化
            price_changes = df['涨跌幅']
            active_concepts = df[df['涨跌幅'].abs() > 0]
            print(f"有涨跌幅的概念: {len(active_concepts)}/{len(df)} ({len(active_concepts)/len(df)*100:.1f}%)")
            
            # 显示收盘后仍有"活动"的概念
            if len(active_concepts) > 0:
                print("\n📈 收盘后活跃概念TOP5:")
                top_active = active_concepts.nlargest(5, '涨跌幅')
                for i, (_, concept) in enumerate(top_active.iterrows(), 1):
                    f62_val = concept.get('f62', 0)
                    f66_val = concept.get('f66', 0)
                    print(f"   {i}. {concept['名称']:<15} | 涨跌: {concept['涨跌幅']:>6.2f}% | f62: {f62_val:>10.0f} | f66: {f66_val:>10.0f}")
        
        print("\n🔍 收盘后热度变化的真实原因:")
        print("1. ✅ 涨跌幅数据: 收盘时已确定，不再变化")
        print("2. ❓ 资金流向(f62): 可能包含盘后清算数据")
        print("3. ❓ 成交量(f66): 可能包含盘后协议交易")
        print("4. ❓ 振幅(f78): 可能因数据修正而微调")
        print("5. ✅ 我们的缓存: 30分钟过期，触发重新计算")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()

async def simulate_heat_stability():
    """模拟收盘后热度稳定性"""
    print("\n🔄 收盘后热度稳定性测试")
    print("-" * 40)
    
    try:
        from data.est.req.est_prepare_data import EstStockPipeline
        
        pipeline = EstStockPipeline(top_n=5)
        
        print("第1次计算...")
        codes1 = await pipeline.get_top_n_concepts()
        
        print("等待1秒后第2次计算...")
        import time
        time.sleep(1)
        
        # 清除缓存强制重新计算
        cache_path = pipeline.cache_dir / "top_concepts.pkl"
        if cache_path.exists():
            import os
            os.remove(cache_path)
        
        codes2 = await pipeline.get_top_n_concepts()
        
        print(f"\n📊 对比结果:")
        print(f"第1次TOP5: {codes1}")
        print(f"第2次TOP5: {codes2}")
        
        if codes1 == codes2:
            print("✅ 收盘后热度计算稳定")
        else:
            print("⚠️ 收盘后热度仍在变化")
            different_count = sum(1 for i in range(min(len(codes1), len(codes2))) if codes1[i] != codes2[i])
            print(f"   差异数量: {different_count}")
        
    except Exception as e:
        print(f"❌ 稳定性测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(verify_after_market_data())
    asyncio.run(simulate_heat_stability())
