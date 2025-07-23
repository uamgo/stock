#!/usr/bin/env python3
"""
调试生产环境和本地环境概念热度差异
"""

from data.est.req.est_concept import EastmoneyConceptStockFetcher
import pandas as pd
import numpy as np

def check_concept_data():
    print("🔍 检查本地概念数据...")
    
    fetcher = EastmoneyConceptStockFetcher()
    df = fetcher.fetch_and_save()
    
    if df is None:
        print("❌ 获取概念数据失败")
        return
    
    print(f"📊 总概念数量: {len(df)}")
    print(f"📊 数据时间戳: {df.get('时间', '未知')}")
    
    # 检查涨跌幅前10名
    print("\n📈 涨跌幅前10名:")
    top10 = df.nlargest(10, '涨跌幅')
    for i, (_, row) in enumerate(top10.iterrows(), 1):
        print(f"  {i:2d}. {row['名称']:<20} | 涨跌: {row['涨跌幅']:>6.2f}% | 代码: {row['代码']}")
    
    # 检查生产环境出现的概念
    prod_concepts = ['昨日连板_含一字', '雅下水电概念', 'CRO', 'CAR-T细胞疗法', '高带宽内存']
    print("\n🔍 检查生产环境热门概念:")
    for concept_name in prod_concepts:
        if concept_name in df['名称'].values:
            concept = df[df['名称'] == concept_name].iloc[0]
            print(f"  ✅ {concept_name:<20} | 涨跌: {concept['涨跌幅']:>6.2f}% | f62: {concept.get('f62', 0)} | f66: {concept.get('f66', 0)}")
        else:
            print(f"  ❌ {concept_name:<20} | 不存在")
    
    # 计算热度分数（使用相同算法）
    print("\n🔥 计算热度分数...")
    results = []
    
    for _, concept in df.iterrows():
        # 1. 板块涨跌幅得分 (40%)
        price_change = concept.get('涨跌幅', 0)
        price_score = np.clip((price_change + 10) * 5, 0, 100)
        
        # 2. 主力资金净流入得分 (30%)
        capital_flow = concept.get('f62', 0) / 100000000  # 转换为亿元
        capital_score = np.clip(capital_flow * 2 + 50, 0, 100)
        
        # 3. 成交活跃度得分 (20%)
        volume = abs(concept.get('f66', 0)) / 100000000  # 转换为亿元
        volume_score = np.clip(np.log10(volume + 1) * 20, 0, 100)
        
        # 4. 技术指标得分 (10%) - 基于振幅
        amplitude = abs(concept.get('f78', 0)) / 1000000
        tech_score = np.clip(amplitude * 5, 0, 100)
        
        # 加权计算总热度
        total_heat = (price_score * 0.4 + capital_score * 0.3 + 
                      volume_score * 0.2 + tech_score * 0.1)
        
        results.append({
            '名称': concept['名称'],
            '代码': concept['代码'],
            '涨跌幅': concept['涨跌幅'],
            '热度分数': round(total_heat, 1),
            'f62': concept.get('f62', 0),
            'f66': concept.get('f66', 0),
            'f78': concept.get('f78', 0)
        })
    
    # 按热度排序
    results_df = pd.DataFrame(results)
    top_heat = results_df.nlargest(10, '热度分数')
    
    print("\n🔥 本地热度排名前10:")
    for i, (_, row) in enumerate(top_heat.iterrows(), 1):
        print(f"  {i:2d}. {row['名称']:<20} | 涨跌: {row['涨跌幅']:>6.2f}% | 热度: {row['热度分数']:>5.1f}分")
    
    # 检查生产环境概念的热度
    print("\n🔍 生产环境概念的本地热度:")
    for concept_name in prod_concepts:
        concept_row = results_df[results_df['名称'] == concept_name]
        if not concept_row.empty:
            row = concept_row.iloc[0]
            print(f"  {concept_name:<20} | 涨跌: {row['涨跌幅']:>6.2f}% | 热度: {row['热度分数']:>5.1f}分")

if __name__ == "__main__":
    check_concept_data()
