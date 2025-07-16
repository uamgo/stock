#!/usr/bin/env python3
"""
补涨概率计算示例
"""

from tail_trading.config.trading_config import TradingConfig

def calculate_probability_example():
    """计算补涨概率示例"""
    config = TradingConfig.get_preset('balanced')
    
    print('=== 当前配置权重 ===')
    print(f'价格权重: {config.price_weight}')
    print(f'成交量权重: {config.volume_weight}')
    print(f'技术形态权重: {config.technical_weight}')
    print(f'位置权重: {config.position_weight}')
    print()
    
    print('=== 补涨概率计算示例 ===')
    
    # 模拟汉宇集团的数据
    stock_data = {
        "name": "汉宇集团",
        "pct_chg": 2.15,
        "volume_ratio": 1.53,
        "shadow_ratio": 0.6,  # 假设下影线/实体 = 0.6
        "position_ratio": 0.833,  # 83.3%
        "trend_slope": 0.5  # 弱势上涨
    }
    
    score = 0
    
    # 1. 涨跌幅评分
    pct_chg = stock_data["pct_chg"]
    if 2.0 <= pct_chg <= 4.0:
        price_score = 25 * config.price_weight
    elif 1.0 <= pct_chg < 2.0:
        price_score = 20 * config.price_weight
    elif 4.0 < pct_chg <= 6.0:
        price_score = 15 * config.price_weight
    else:
        price_score = 0
    
    # 2. 量比评分
    volume_ratio = stock_data["volume_ratio"]
    if 1.5 <= volume_ratio <= 2.5:
        volume_score = 25 * config.volume_weight
    elif 1.2 <= volume_ratio < 1.5:
        volume_score = 20 * config.volume_weight
    elif 2.5 < volume_ratio <= 3.0:
        volume_score = 15 * config.volume_weight
    else:
        volume_score = 10 * config.volume_weight
    
    # 3. 技术形态评分
    shadow_ratio = stock_data["shadow_ratio"]
    if shadow_ratio >= 0.8:
        tech_score = 25 * config.technical_weight
    elif shadow_ratio >= 0.5:
        tech_score = 20 * config.technical_weight
    elif shadow_ratio >= 0.2:
        tech_score = 15 * config.technical_weight
    else:
        tech_score = 10 * config.technical_weight
    
    # 4. 位置评分
    position_ratio = stock_data["position_ratio"]
    if position_ratio <= 0.4:
        pos_score = 20 * config.position_weight
    elif position_ratio <= 0.6:
        pos_score = 15 * config.position_weight
    elif position_ratio <= 0.8:
        pos_score = 10 * config.position_weight
    else:
        pos_score = 5 * config.position_weight
    
    # 5. 趋势评分
    trend_slope = stock_data["trend_slope"]
    if trend_slope > 1:
        trend_score = 5
    elif trend_slope > 0:
        trend_score = 3
    else:
        trend_score = 0
    
    total_score = price_score + volume_score + tech_score + pos_score + trend_score
    
    print(f'股票: {stock_data["name"]}')
    print(f'涨跌幅评分: {price_score:.2f}分 (涨幅{pct_chg}%)')
    print(f'量比评分: {volume_score:.2f}分 (量比{volume_ratio}倍)')
    print(f'技术形态评分: {tech_score:.2f}分 (影线比{shadow_ratio})')
    print(f'位置评分: {pos_score:.2f}分 (位置{position_ratio*100:.1f}%)')
    print(f'趋势评分: {trend_score}分')
    print(f'总分: {total_score:.2f}分')
    
    print()
    print('=== 评分区间解释 ===')
    print('🟢 25-30分: 高概率 (优先选择)')
    print('🟡 20-24分: 中等概率 (谨慎操作)')
    print('🟠 15-19分: 较低概率 (建议观望)')
    print('🔴 <15分: 低概率 (避免操作)')

if __name__ == "__main__":
    calculate_probability_example()
