#!/usr/bin/env python3
"""
收盘后热度变化分析脚本
分析为什么A股收盘(15:00)后热度还会变化
"""

import os
import asyncio
from datetime import datetime, time
import pandas as pd

async def analyze_after_market_heat_change():
    """分析收盘后热度变化的原因"""
    print("🕒 收盘后热度变化分析")
    print("=" * 60)
    
    current_time = datetime.now()
    print(f"📍 当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # A股交易时间
    market_open = time(9, 30)
    market_close = time(15, 0)
    current_time_only = current_time.time()
    
    if current_time_only > market_close:
        print("📈 A股市场已收盘")
        time_after_close = (datetime.combine(current_time.date(), current_time_only) - 
                           datetime.combine(current_time.date(), market_close)).total_seconds() / 60
        print(f"⏰ 收盘后已过: {time_after_close:.0f}分钟")
    else:
        print("📈 A股市场交易中")
    
    print("\n🔍 收盘后热度变化的可能原因:")
    
    reasons = [
        {
            "原因": "数据源更新延迟",
            "说明": "东方财富等数据源在收盘后仍在处理和更新数据",
            "影响": "f62(资金流向)、f66(成交额)等字段可能延迟更新",
            "时间窗口": "收盘后5-30分钟"
        },
        {
            "原因": "盘后交易数据",
            "说明": "虽然A股主板收盘，但可能包含盘后协议交易数据",
            "影响": "成交量和资金流向数据发生变化",
            "时间窗口": "收盘后30分钟内"
        },
        {
            "原因": "数据清算和校正",
            "说明": "交易所和数据商在收盘后进行数据清算",
            "影响": "修正交易期间的异常数据",
            "时间窗口": "收盘后1-2小时"
        },
        {
            "原因": "跨市场数据同步",
            "说明": "港股、美股等相关市场仍在交易，影响概念热度",
            "影响": "相关概念的热度受海外市场影响",
            "时间窗口": "全天候"
        },
        {
            "原因": "算法缓存更新",
            "说明": "我们的缓存机制在收盘后重新计算热度",
            "影响": "缓存过期触发重新计算",
            "时间窗口": "缓存过期时(30分钟)"
        }
    ]
    
    for i, reason in enumerate(reasons, 1):
        print(f"\n{i}. {reason['原因']}")
        print(f"   📝 说明: {reason['说明']}")
        print(f"   📊 影响: {reason['影响']}")
        print(f"   ⏱️ 时间窗口: {reason['时间窗口']}")
    
    print("\n🔬 验证分析:")
    
    try:
        from data.est.req.est_concept import EastmoneyConceptStockFetcher
        
        print("正在获取当前概念数据...")
        fetcher = EastmoneyConceptStockFetcher()
        df = fetcher.fetch_and_save()
        
        if df is not None:
            print(f"✅ 成功获取 {len(df)} 个概念数据")
            
            # 检查数据时间戳
            if 'timestamp' in df.columns:
                print(f"📅 数据时间戳: {df['timestamp'].iloc[0] if not df['timestamp'].empty else '未知'}")
            
            # 分析数据特征
            print("\n📊 当前数据特征:")
            
            # 检查是否有交易量
            has_volume = df['f66'].abs().sum() > 0
            print(f"📈 是否有成交量数据: {'是' if has_volume else '否'}")
            
            # 检查资金流向
            has_capital_flow = df['f62'].abs().sum() > 0
            print(f"💰 是否有资金流向数据: {'是' if has_capital_flow else '否'}")
            
            # 检查涨跌幅分布
            price_changes = df['涨跌幅']
            print(f"📊 涨跌幅统计:")
            print(f"   最大涨幅: {price_changes.max():.2f}%")
            print(f"   最大跌幅: {price_changes.min():.2f}%")
            print(f"   平均涨跌幅: {price_changes.mean():.2f}%")
            
            # 检查数据是否"冻结"
            zero_volume_count = (df['f66'] == 0).sum()
            zero_capital_count = (df['f62'] == 0).sum()
            
            print(f"\n🧊 数据'冻结'检查:")
            print(f"   零成交量概念数: {zero_volume_count}/{len(df)} ({zero_volume_count/len(df)*100:.1f}%)")
            print(f"   零资金流向概念数: {zero_capital_count}/{len(df)} ({zero_capital_count/len(df)*100:.1f}%)")
            
            if zero_volume_count > len(df) * 0.8:
                print("   ⚠️ 大部分概念成交量为0，可能是收盘后数据")
            else:
                print("   ✅ 数据显示市场仍有活跃度")
        
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
    
    print("\n💡 建议解决方案:")
    solutions = [
        "添加市场时间检查，收盘后降低数据更新频率",
        "在热度计算中添加数据时间戳验证",
        "收盘后使用更长的缓存时间(如2小时)",
        "为收盘后数据添加特殊标识",
        "实现数据稳定性检查，避免频繁变化"
    ]
    
    for i, solution in enumerate(solutions, 1):
        print(f"{i}. {solution}")

def create_market_time_checker():
    """创建市场时间检查器"""
    print(f"\n🕒 市场时间检查器")
    print("-" * 30)
    
    from datetime import datetime, time
    
    now = datetime.now()
    current_time = now.time()
    
    # A股交易时间
    morning_open = time(9, 30)
    morning_close = time(11, 30)
    afternoon_open = time(13, 0)
    afternoon_close = time(15, 0)
    
    print(f"当前时间: {current_time}")
    
    if morning_open <= current_time <= morning_close:
        print("🟢 上午交易时段")
        return "morning_trading"
    elif morning_close < current_time < afternoon_open:
        print("🟡 午间休市")
        return "lunch_break"
    elif afternoon_open <= current_time <= afternoon_close:
        print("🟢 下午交易时段")
        return "afternoon_trading"
    else:
        print("🔴 收盘时段")
        return "after_market"

if __name__ == "__main__":
    asyncio.run(analyze_after_market_heat_change())
    create_market_time_checker()
