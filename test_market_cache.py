#!/usr/bin/env python3
"""
测试市场时间感知缓存效果
验证收盘后热度计算的稳定性改进
"""

import asyncio
import os
from datetime import datetime

async def test_market_aware_cache():
    """测试市场时间感知缓存"""
    print("🔍 市场时间感知缓存测试")
    print("=" * 50)
    
    current_time = datetime.now()
    print(f"📍 当前时间: {current_time.strftime('%H:%M:%S')}")
    
    try:
        from data.est.req.est_prepare_data import EstStockPipeline
        
        pipeline = EstStockPipeline(top_n=5)
        
        # 测试市场状态检测
        print(f"\n🕒 市场状态检测:")
        print(f"   是否开市: {pipeline.is_market_open()}")
        print(f"   市场状态: {pipeline.get_market_status()}")
        print(f"   缓存时长: {pipeline.get_cache_duration()}秒 ({pipeline.get_cache_duration()//3600}小时{(pipeline.get_cache_duration()%3600)//60}分钟)")
        
        # 清除缓存，测试第一次计算
        cache_path = pipeline.cache_dir / "top_concepts.pkl"
        if cache_path.exists():
            os.remove(cache_path)
            print("\n🗑️ 已清除缓存，准备重新计算")
        
        print("\n🔄 第一次热度计算 (应该重新计算):")
        codes1 = await pipeline.get_top_n_concepts()
        
        print(f"\n⏱️ 等待2秒后进行第二次计算...")
        import time
        time.sleep(2)
        
        print("\n🔄 第二次热度计算 (应该使用缓存):")
        codes2 = await pipeline.get_top_n_concepts()
        
        print(f"\n📊 测试结果:")
        print(f"第一次TOP5: {codes1}")
        print(f"第二次TOP5: {codes2}")
        
        if codes1 == codes2:
            print("✅ 缓存机制工作正常，热度保持稳定")
        else:
            print("❌ 缓存机制异常，热度发生变化")
        
        # 测试缓存信息
        if cache_path.exists():
            cache_mtime = os.path.getmtime(cache_path)
            cache_age = (datetime.now().timestamp() - cache_mtime) / 60
            print(f"💾 缓存状态: 存在，年龄 {cache_age:.1f} 分钟")
            
            # 预测下次更新时间
            next_update_minutes = pipeline.get_cache_duration() / 60 - cache_age
            if next_update_minutes > 0:
                print(f"⏰ 预计 {next_update_minutes:.0f} 分钟后缓存过期，重新计算")
            else:
                print("⚠️ 缓存已过期但仍在使用（异常）")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_market_time_detection():
    """测试市场时间检测的准确性"""
    print(f"\n🕒 市场时间检测测试")
    print("-" * 30)
    
    from datetime import time
    from data.est.req.est_prepare_data import EstStockPipeline
    
    pipeline = EstStockPipeline()
    
    # 测试用例
    test_cases = [
        ("9:29", "开盘前", False),
        ("9:30", "开盘", True),
        ("10:30", "上午交易", True),
        ("11:30", "上午收盘", True),
        ("11:31", "午休", False),
        ("12:59", "午休结束前", False),
        ("13:00", "下午开盘", True),
        ("14:30", "下午交易", True),
        ("15:00", "收盘", True),
        ("15:01", "收盘后", False),
        ("18:30", "深度收盘后", False)
    ]
    
    print("时间点测试:")
    for time_str, desc, expected in test_cases:
        # 这里只是显示逻辑，实际需要模拟时间
        print(f"   {time_str} ({desc}): 预期{'开市' if expected else '闭市'}")
    
    # 显示当前实际状态
    current_status = pipeline.get_market_status()
    is_open = pipeline.is_market_open()
    cache_duration = pipeline.get_cache_duration()
    
    print(f"\n当前实际状态:")
    print(f"   市场状态: {current_status}")
    print(f"   是否开市: {'是' if is_open else '否'}")
    print(f"   缓存策略: {cache_duration//3600}小时" if cache_duration >= 3600 else f"{cache_duration//60}分钟")

if __name__ == "__main__":
    asyncio.run(test_market_aware_cache())
    test_market_time_detection()
