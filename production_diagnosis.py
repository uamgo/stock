#!/usr/bin/env python3
"""
生产环境诊断脚本 - 检查热度计算问题
"""

import sys
import os

# 添加路径
sys.path.append('/home/uamgo/stock')

def diagnose_production():
    print("🔍 生产环境诊断开始...")
    print(f"📍 当前工作目录: {os.getcwd()}")
    print(f"📍 Python路径: {sys.executable}")
    print(f"📍 Python版本: {sys.version}")
    
    try:
        print("\n1️⃣ 测试导入模块...")
        from data.est.req.est_concept import EastmoneyConceptStockFetcher
        print("✅ EastmoneyConceptStockFetcher 导入成功")
        
        from data.est.req.est_prepare_data import EstStockPipeline
        print("✅ EstStockPipeline 导入成功")
        
        import numpy as np
        print("✅ numpy 导入成功")
        
        import pandas as pd
        print("✅ pandas 导入成功")
        
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return
    
    try:
        print("\n2️⃣ 测试概念数据获取...")
        fetcher = EastmoneyConceptStockFetcher()
        df = fetcher.fetch_and_save()
        
        if df is not None:
            print(f"✅ 概念数据获取成功，共 {len(df)} 个概念")
            print(f"📊 涨跌幅前3名:")
            top3 = df.nlargest(3, '涨跌幅')
            for i, (_, row) in enumerate(top3.iterrows(), 1):
                print(f"   {i}. {row['名称']:<20} | 涨跌: {row['涨跌幅']:>6.2f}%")
        else:
            print("❌ 概念数据获取失败")
            return
            
    except Exception as e:
        print(f"❌ 概念数据获取异常: {e}")
        return
    
    try:
        print("\n3️⃣ 测试热度计算...")
        pipeline = EstStockPipeline(top_n=5)
        
        # 手动调用热度计算
        df_with_heat = pipeline.calculate_concept_heat(df)
        
        print("✅ 热度计算成功")
        print("📊 热度排名前5:")
        top5_heat = df_with_heat.nlargest(5, "热度分数")
        for i, (_, row) in enumerate(top5_heat.iterrows(), 1):
            print(f"   {i}. {row['名称']:<20} | 涨跌: {row['涨跌幅']:>6.2f}% | 热度: {row['热度分数']:>5.1f}分")
        
    except Exception as e:
        print(f"❌ 热度计算异常: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ 生产环境诊断完成")

if __name__ == "__main__":
    diagnose_production()
