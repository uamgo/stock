#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富接口字段详细分析工具
分析所有字段的含义、数据类型和取值范围
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_eastmoney_fields():
    """分析东方财富概念股数据字段"""
    
    # 数据文件路径
    data_path = "/tmp/stock/base/eastmoney_concept_stocks.pkl"
    
    if not os.path.exists(data_path):
        print("❌ 数据文件不存在，请先运行概念股数据获取程序")
        return
    
    # 读取数据
    df = pd.read_pickle(data_path)
    print(f"📊 分析数据：{len(df)} 条记录，{len(df.columns)} 个字段")
    print("="*100)
    
    # 东方财富API字段映射表（基于实际数据结构分析）
    field_mappings = {
        # 基础信息字段
        "f1": {"name": "市场标识", "desc": "交易所代码", "type": "int", "example": "0=深圳,1=上海,2=其他"},
        "f12": {"name": "股票代码", "desc": "6位股票代码", "type": "string"},
        "f13": {"name": "市场简码", "desc": "市场编号", "type": "int"},
        "f14": {"name": "股票名称", "desc": "股票简称", "type": "string"},
        
        # 价格相关字段
        "f2": {"name": "最新价", "desc": "当前价格", "type": "float", "unit": "元"},
        "f3": {"name": "涨跌幅", "desc": "今日涨跌幅", "type": "float", "unit": "%"},
        "f4": {"name": "涨跌额", "desc": "今日涨跌额", "type": "float", "unit": "元"},
        "f5": {"name": "成交量", "desc": "今日成交量", "type": "float", "unit": "手"},
        "f6": {"name": "成交额", "desc": "今日成交金额", "type": "float", "unit": "元"},
        
        # 技术分析字段
        "f15": {"name": "最高价", "desc": "今日最高价", "type": "float", "unit": "元"},
        "f16": {"name": "最低价", "desc": "今日最低价", "type": "float", "unit": "元"},
        "f17": {"name": "今开", "desc": "今日开盘价", "type": "float", "unit": "元"},
        "f18": {"name": "昨收", "desc": "昨日收盘价", "type": "float", "unit": "元"},
        
        # 资金流向字段
        "f62": {"name": "主力净流入", "desc": "主力资金净流入", "type": "float", "unit": "元"},
        "f66": {"name": "成交额_重复", "desc": "成交金额(可能重复)", "type": "float", "unit": "元"},
        "f69": {"name": "换手率", "desc": "换手率", "type": "float", "unit": "%"},
        "f72": {"name": "平均价", "desc": "均价", "type": "float", "unit": "元"},
        "f75": {"name": "量比", "desc": "量比", "type": "float"},
        "f78": {"name": "振幅", "desc": "振幅", "type": "float", "unit": "%"},
        
        # 估值字段
        "f81": {"name": "总市值", "desc": "总市值", "type": "float", "unit": "元"},
        "f84": {"name": "市盈率", "desc": "市盈率TTM", "type": "float"},
        "f87": {"name": "流通市值", "desc": "流通市值", "type": "float", "unit": "元"},
        "f116": {"name": "总股本", "desc": "总股本", "type": "float", "unit": "股"},
        "f117": {"name": "流通股", "desc": "流通股本", "type": "float", "unit": "股"},
        
        # 时间和状态字段
        "f124": {"name": "更新时间", "desc": "数据更新时间戳", "type": "timestamp"},
        "f184": {"name": "概念名称", "desc": "所属概念板块", "type": "string"},
        "f204": {"name": "涨速", "desc": "涨跌速度", "type": "float", "unit": "%"},
        "f205": {"name": "5分钟涨跌", "desc": "5分钟涨跌", "type": "float", "unit": "%"},
        "f206": {"name": "60日涨跌幅", "desc": "60日涨跌幅", "type": "float", "unit": "%"},
        "f207": {"name": "年初至今涨跌幅", "desc": "年初至今涨跌幅", "type": "float", "unit": "%"},
        
        # 其他字段
        "代码": {"name": "概念代码", "desc": "概念板块代码", "type": "string"},
        "名称": {"name": "概念名称_中文", "desc": "概念板块中文名", "type": "string"},
        "涨跌幅": {"name": "板块涨跌幅", "desc": "概念板块涨跌幅", "type": "float", "unit": "%"},
        "概念名称": {"name": "个股概念", "desc": "个股所属概念", "type": "string"}
    }
    
    print("🔍 字段详细分析:")
    print("-" * 100)
    print(f"{'字段代码':<10} {'字段名称':<15} {'描述':<25} {'数据类型':<10} {'示例值':<20}")
    print("-" * 100)
    
    # 分析每个字段
    for col in df.columns:
        if col in field_mappings:
            field_info = field_mappings[col]
            field_name = field_info["name"]
            field_desc = field_info["desc"]
            field_type = field_info["type"]
            unit = field_info.get("unit", "")
        else:
            field_name = "未知字段"
            field_desc = "待分析"
            field_type = "unknown"
            unit = ""
        
        # 获取示例值
        sample_values = df[col].dropna().head(3).tolist()
        if len(sample_values) > 0:
            if field_type == "timestamp":
                try:
                    timestamp = int(sample_values[0])
                    dt = datetime.fromtimestamp(timestamp)
                    example = f"{timestamp} ({dt.strftime('%H:%M:%S')})"
                except:
                    example = str(sample_values[0])
            elif field_type == "float" and unit:
                try:
                    example = f"{float(sample_values[0]):.2f} {unit}"
                except:
                    example = str(sample_values[0])
            else:
                example = str(sample_values[0])
        else:
            example = "无数据"
        
        print(f"{col:<10} {field_name:<15} {field_desc:<25} {field_type:<10} {example:<20}")
    
    print("-" * 100)
    
    # 数据质量分析
    print(f"\n📈 数据质量分析:")
    print("-" * 60)
    print(f"{'字段':<10} {'非空数量':<10} {'空值数量':<10} {'完整度':<10} {'唯一值数':<10}")
    print("-" * 60)
    
    for col in df.columns:
        non_null = df[col].count()
        null_count = len(df) - non_null
        completeness = f"{(non_null/len(df)*100):.1f}%"
        unique_count = df[col].nunique()
        print(f"{col:<10} {non_null:<10} {null_count:<10} {completeness:<10} {unique_count:<10}")
    
    # 数值字段统计
    print(f"\n📊 数值字段统计:")
    print("-" * 80)
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if col in field_mappings:
            field_name = field_mappings[col]["name"]
            unit = field_mappings[col].get("unit", "")
        else:
            field_name = col
            unit = ""
        
        stats = df[col].describe()
        print(f"\n{col} ({field_name}):")
        print(f"  最小值: {stats['min']:.2f} {unit}")
        print(f"  最大值: {stats['max']:.2f} {unit}")
        print(f"  平均值: {stats['mean']:.2f} {unit}")
        print(f"  中位数: {stats['50%']:.2f} {unit}")
    
    # 分析概念分布
    if '概念名称' in df.columns:
        print(f"\n🏷️ 概念分布分析:")
        print("-" * 60)
        concept_counts = df['概念名称'].value_counts().head(10)
        print("前10个最热门概念:")
        for concept, count in concept_counts.items():
            print(f"  {concept}: {count} 只股票")
    
    # 分析涨跌幅分布
    if '涨跌幅' in df.columns:
        print(f"\n📈 涨跌幅分布:")
        print("-" * 40)
        up_count = len(df[df['涨跌幅'] > 0])
        down_count = len(df[df['涨跌幅'] < 0])
        flat_count = len(df[df['涨跌幅'] == 0])
        print(f"上涨概念: {up_count} 个 ({up_count/len(df)*100:.1f}%)")
        print(f"下跌概念: {down_count} 个 ({down_count/len(df)*100:.1f}%)")
        print(f"平盘概念: {flat_count} 个 ({flat_count/len(df)*100:.1f}%)")
    
    print("\n" + "="*100)
    print(f"✅ 分析完成！共分析了 {len(df)} 条记录，{len(df.columns)} 个字段")

if __name__ == "__main__":
    analyze_eastmoney_fields()
