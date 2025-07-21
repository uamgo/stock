#!/usr/bin/env python3
"""
传统选股脚本 - 基于技术指标的经典选股

使用传统的技术指标进行选股，注重技术形态和量价关系
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tail_trading.strategies.tail_up_strategy import TailUpStrategy
from tail_trading.config.trading_config import TradingConfig
import pandas as pd
import json
from datetime import datetime

def main():
    print("📊 启动传统技术指标选股系统...")
    print("🎯 基于经典技术指标和量价关系")
    
    try:
        # 1. 使用平衡配置进行传统选股
        print("\n🔍 执行传统技术指标选股...")
        trading_config = TradingConfig.get_preset("balanced")
        strategy = TailUpStrategy(trading_config)
        
        all_stocks = strategy.select_stocks()
        
        if all_stocks is None or all_stocks.empty:
            print("❌ 传统选股没有找到合适的股票")
            return
        
        print(f"传统选股完成，共找到 {len(all_stocks)} 只候选股票")
        
        # 2. 应用传统技术指标筛选
        print("\n📈 应用传统技术指标筛选...")
        filtered_stocks = apply_traditional_filters(all_stocks)
        
        print(f"✅ 最终筛选出 {len(filtered_stocks)} 只股票")
        
        # 3. 显示结果
        if not filtered_stocks.empty:
            print("\n📋 传统选股结果（按技术评分排序）：")
            for i, (_, stock) in enumerate(filtered_stocks.head(10).iterrows()):
                print(f"{i+1}. {stock['代码']} {stock.get('名称', '')} - 技术评分：{stock.get('technical_score', 0):.1f}分")
        
        # 4. 输出结果供前端使用
        result_data = []
        for _, stock in filtered_stocks.head(10).iterrows():
            result_data.append({
                "代码": stock['代码'],
                "名称": stock.get('名称', ''),
                "涨跌幅": stock.get('涨跌幅', 0),
                "技术评分": round(stock.get('technical_score', 0), 1),
                "风险评分": round(stock.get('风险评分', 30), 1),  # 添加风险评分字段
                "选股类型": "传统技术指标"
            })
        
        # 5. 输出JSON格式结果
        output = {
            "success": True,
            "strategy": "traditional",
            "count": len(result_data),
            "stocks": result_data,
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "="*50)
        print("📊 传统选股结果（JSON格式）：")
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ 传统选股失败：{e}")
        error_output = {
            "success": False,
            "strategy": "traditional",
            "error": str(e),
            "stocks": [],
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_output, ensure_ascii=False))

def apply_traditional_filters(stocks_df: pd.DataFrame) -> pd.DataFrame:
    """
    应用传统技术指标筛选
    
    Args:
        stocks_df: 原始股票数据
        
    Returns:
        筛选后的股票数据
    """
    if stocks_df.empty:
        return stocks_df
    
    # 复制数据
    filtered_df = stocks_df.copy()
    
    # 1. 传统技术指标评分
    filtered_df['technical_score'] = 0
    
    # 基于涨跌幅的评分（传统偏好适中涨幅）
    filtered_df.loc[filtered_df['涨跌幅'].between(1, 4), 'technical_score'] += 20
    filtered_df.loc[filtered_df['涨跌幅'].between(4, 6), 'technical_score'] += 15
    filtered_df.loc[filtered_df['涨跌幅'].between(0, 1), 'technical_score'] += 10
    
    # 基于20日位置的评分（传统偏好中等位置）
    if '20日位置' in filtered_df.columns:
        filtered_df.loc[filtered_df['20日位置'].between(40, 70), 'technical_score'] += 25
        filtered_df.loc[filtered_df['20日位置'].between(70, 85), 'technical_score'] += 20
        filtered_df.loc[filtered_df['20日位置'].between(20, 40), 'technical_score'] += 15
    
    # 基于次日补涨概率的评分
    if '次日补涨概率' in filtered_df.columns:
        filtered_df.loc[filtered_df['次日补涨概率'] >= 25, 'technical_score'] += 30
        filtered_df.loc[filtered_df['次日补涨概率'].between(20, 25), 'technical_score'] += 20
        filtered_df.loc[filtered_df['次日补涨概率'].between(15, 20), 'technical_score'] += 10
    
    # 基于风险评分的调整（传统策略偏保守）
    if '风险评分' in filtered_df.columns:
        filtered_df.loc[filtered_df['风险评分'] <= 40, 'technical_score'] += 15
        filtered_df.loc[filtered_df['风险评分'].between(40, 60), 'technical_score'] += 10
        filtered_df.loc[filtered_df['风险评分'] > 60, 'technical_score'] -= 10
    
    # 2. 筛选条件：技术评分 >= 40分
    filtered_df = filtered_df[filtered_df['technical_score'] >= 40]
    
    # 3. 按技术评分排序
    filtered_df = filtered_df.sort_values('technical_score', ascending=False)
    
    return filtered_df.reset_index(drop=True)

if __name__ == "__main__":
    main()
