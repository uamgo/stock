#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
概念热度计算方法详细解释工具 (基于新字段分析)
根据实际数据结构重新设计热度计算方法
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_concept_heat_v2():
    """基于新字段分析的概念热度计算方法"""
    
    print("🔥 概念热度计算方法详解 (基于新字段分析)")
    print("="*80)
    
    # 读取数据
    data_path = "/tmp/stock/base/eastmoney_concept_stocks.pkl"
    if not os.path.exists(data_path):
        print("❌ 数据文件不存在")
        return
    
    df = pd.read_pickle(data_path)
    print(f"📊 数据概览: {len(df)} 个概念板块")
    
    # 根据实际数据结构重新定义字段映射
    field_mapping = {
        "f1": "市场标识",     # 交易所标识
        "f2": "概念指数",     # 概念板块指数值
        "涨跌幅": "板块涨跌幅",  # 概念板块涨跌幅 (%)
        "代码": "概念代码",     # 概念板块代码 (BKxxxx)
        "f13": "市场代码",    # 市场编号
        "名称": "概念名称",     # 概念板块名称
        "f62": "主力净流入",   # 主力资金净流入 (元)
        "f66": "成交额",      # 成交金额 (元)
        "f69": "换手率",      # 换手率 (%)
        "f72": "平均价",      # 平均价格
        "f75": "量比",        # 量比
        "f78": "振幅",        # 振幅 (%)
        "f81": "总市值",      # 总市值相关
        "f84": "市盈率",      # 市盈率相关
        "f87": "流通市值",    # 流通市值相关
        "f124": "更新时间",   # 数据更新时间戳
        "概念名称": "个股概念", # 个股涨跌数据
        "f204": "龙头股票",   # 龙头股票名称
        "f205": "龙头代码",   # 龙头股票代码
        "f206": "其他标识"    # 其他标识
    }
    
    print("\n📈 新版热度计算方法:")
    print("-" * 60)
    print("基于实际数据结构，采用以下4个维度计算概念热度：")
    print("1. 板块涨跌幅 (40%) - 反映概念整体表现")
    print("2. 主力资金净流入 (30%) - 反映资金关注度")
    print("3. 成交活跃度 (20%) - 反映市场参与度")
    print("4. 技术指标 (10%) - 反映技术面强度")
    
    # 数据预处理
    print("\n🔧 数据预处理:")
    print("-" * 40)
    
    # 检查关键字段
    key_fields = ["涨跌幅", "f62", "f66", "f78"]
    for field in key_fields:
        if field in df.columns:
            valid_count = df[field].count()
            print(f"✓ {field_mapping.get(field, field)}: {valid_count}/{len(df)} 有效数据")
        else:
            print(f"✗ {field} 字段缺失")
    
    # 计算热度分数
    print("\n🧮 热度计算过程:")
    print("-" * 40)
    
    # 1. 板块涨跌幅得分 (40%)
    if "涨跌幅" in df.columns:
        price_change = df["涨跌幅"].fillna(0)
        # 标准化到0-100分
        price_score = np.clip((price_change + 10) * 5, 0, 100)  # -10%~+10% 映射到 0~100分
        print(f"1. 板块涨跌幅得分: 平均 {price_score.mean():.1f}分")
    else:
        price_score = pd.Series([0] * len(df))
        print("1. 板块涨跌幅得分: 数据缺失，设为0分")
    
    # 2. 主力资金净流入得分 (30%)
    if "f62" in df.columns:
        capital_flow = df["f62"].fillna(0)
        # 将资金流入转换为得分 (亿元为单位)
        capital_flow_yi = capital_flow / 100000000  # 转换为亿元
        capital_score = np.clip(capital_flow_yi * 2 + 50, 0, 100)  # 大致映射到0-100分
        print(f"2. 主力资金得分: 平均 {capital_score.mean():.1f}分")
    else:
        capital_score = pd.Series([0] * len(df))
        print("2. 主力资金得分: 数据缺失，设为0分")
    
    # 3. 成交活跃度得分 (20%)
    if "f66" in df.columns:
        volume = df["f66"].fillna(0)
        # 成交额标准化
        volume_yi = abs(volume) / 100000000  # 转换为亿元，取绝对值
        volume_score = np.clip(np.log10(volume_yi + 1) * 20, 0, 100)  # 对数缩放
        print(f"3. 成交活跃度得分: 平均 {volume_score.mean():.1f}分")
    else:
        volume_score = pd.Series([0] * len(df))
        print("3. 成交活跃度得分: 数据缺失，设为0分")
    
    # 4. 技术指标得分 (10%) - 基于振幅
    if "f78" in df.columns:
        amplitude = df["f78"].fillna(0)
        # 振幅标准化 (合理范围0-20%)
        tech_score = np.clip(abs(amplitude) / 1000000 * 5, 0, 100)  # 调整缩放比例
        print(f"4. 技术指标得分: 平均 {tech_score.mean():.1f}分")
    else:
        tech_score = pd.Series([0] * len(df))
        print("4. 技术指标得分: 数据缺失，设为0分")
    
    # 加权计算总热度
    total_heat = (price_score * 0.4 + capital_score * 0.3 + 
                  volume_score * 0.2 + tech_score * 0.1)
    
    df["热度分数"] = total_heat
    df["热度等级"] = pd.cut(total_heat, 
                        bins=[0, 20, 40, 60, 80, 100],
                        labels=["极冷", "偏冷", "温和", "偏热", "火热"])
    
    print(f"\n📊 市场热度分布:")
    print("-" * 40)
    heat_distribution = df["热度等级"].value_counts()
    for level, count in heat_distribution.items():
        percentage = count / len(df) * 100
        print(f"{level}: {count} 个概念 ({percentage:.1f}%)")
    
    print(f"\n📈 热度统计:")
    print("-" * 40)
    print(f"平均热度: {total_heat.mean():.2f} 分")
    print(f"最高热度: {total_heat.max():.2f} 分")
    print(f"最低热度: {total_heat.min():.2f} 分")
    
    # 显示热门概念TOP10
    print(f"\n🔥 热门概念TOP10:")
    print("-" * 60)
    top_concepts = df.nlargest(10, "热度分数")[["名称", "涨跌幅", "热度分数", "热度等级"]]
    for idx, row in top_concepts.iterrows():
        concept_name = row["名称"]
        price_change = row["涨跌幅"]
        heat_score = row["热度分数"]
        heat_level = row["热度等级"]
        print(f"{concept_name:<20} | 涨跌: {price_change:>6.2f}% | 热度: {heat_score:>5.1f}分 | {heat_level}")
    
    # 显示冷门概念TOP10
    print(f"\n🧊 冷门概念TOP10:")
    print("-" * 60)
    cold_concepts = df.nsmallest(10, "热度分数")[["名称", "涨跌幅", "热度分数", "热度等级"]]
    for idx, row in cold_concepts.iterrows():
        concept_name = row["名称"]
        price_change = row["涨跌幅"]
        heat_score = row["热度分数"]
        heat_level = row["热度等级"]
        print(f"{concept_name:<20} | 涨跌: {price_change:>6.2f}% | 热度: {heat_score:>5.1f}分 | {heat_level}")
    
    # 详细分析几个典型概念
    print(f"\n🔍 典型概念详细分析:")
    print("="*80)
    
    # 选择几个不同热度等级的概念进行详细分析
    sample_concepts = []
    for level in ["火热", "偏热", "温和", "偏冷", "极冷"]:
        level_concepts = df[df["热度等级"] == level]
        if not level_concepts.empty:
            sample_concepts.append(level_concepts.iloc[0])
    
    for i, concept in enumerate(sample_concepts[:3], 1):
        print(f"\n📋 概念{i}: {concept['名称']} (热度等级: {concept['热度等级']})")
        print("-" * 50)
        
        # 重新计算各维度得分用于展示
        concept_price_change = concept["涨跌幅"]
        concept_capital_flow = concept["f62"] / 100000000  # 亿元
        concept_volume = abs(concept["f66"]) / 100000000   # 亿元
        concept_amplitude = abs(concept["f78"]) / 1000000  # 调整后的振幅
        
        concept_price_score = np.clip((concept_price_change + 10) * 5, 0, 100)
        concept_capital_score = np.clip(concept_capital_flow * 2 + 50, 0, 100)
        concept_volume_score = np.clip(np.log10(concept_volume + 1) * 20, 0, 100)
        concept_tech_score = np.clip(concept_amplitude * 5, 0, 100)
        
        print(f"  板块涨跌幅: {concept_price_change:6.2f}% → {concept_price_score:5.1f}分 (权重40%)")
        print(f"  主力净流入: {concept_capital_flow:6.1f}亿 → {concept_capital_score:5.1f}分 (权重30%)")
        print(f"  成交活跃度: {concept_volume:6.1f}亿 → {concept_volume_score:5.1f}分 (权重20%)")
        print(f"  技术指标:   {concept_amplitude:6.2f}   → {concept_tech_score:5.1f}分 (权重10%)")
        print(f"  总热度分数: {concept['热度分数']:5.1f}分")
    
    print(f"\n📝 使用建议:")
    print("-" * 40)
    print("1. 热度>60分: 关注度高，适合短线操作")
    print("2. 热度40-60分: 中等关注，可适度参与")
    print("3. 热度20-40分: 关注度低，需谨慎操作")
    print("4. 热度<20分: 市场冷淡，建议观望")
    
    # 保存详细分析结果
    output_file = f"/tmp/stock/concept_heat_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df_output = df[["名称", "涨跌幅", "f62", "f66", "热度分数", "热度等级"]].copy()
    df_output.columns = ["概念名称", "涨跌幅(%)", "主力净流入(元)", "成交额(元)", "热度分数", "热度等级"]
    df_output.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n💾 详细分析结果已保存到: {output_file}")
    
    print("\n" + "="*80)
    print("✅ 概念热度分析完成！")

if __name__ == "__main__":
    analyze_concept_heat_v2()
