# 市场强弱判断系统详解

## 🎯 核心问题

您问到"市场强弱是怎么样判断的？"，这是一个非常重要的问题，因为准确的市场强弱判断是选股成功的关键。

## 📊 我们的判断体系

### 1. 数据来源
```
📈 主要指数：
• 上证指数 (SH Index) - 主板市场代表
• 深证成指 (SZ Index) - 深市代表  
• 创业板指 (CY Index) - 成长股代表

📊 关键数据：
• 价格序列（收盘价）
• 成交量数据
• 时间跨度：默认7天，可调整
```

### 2. 趋势方向判断

#### 算法逻辑：
```python
# 计算每日价格变化率
price_changes = [(prices[i] - prices[i-1]) / prices[i-1] * 100 
                 for i in range(1, len(prices))]

# 平均变化率
avg_change = mean(price_changes)

# 判断标准：
if avg_change > 0.5%:   # 上涨
    trend = "上涨"
elif avg_change < -0.5%: # 下跌
    trend = "下跌"  
else:                   # 震荡
    trend = "震荡"
```

#### 实际例子：
```
最近7天收盘价：[3200, 3180, 3220, 3250, 3260, 3280, 3290]
价格变化率：[-0.63%, +1.26%, +1.36%, +0.31%, +0.77%, +0.30%]
平均变化率：+0.56% > 0.5% → 判断为"上涨"
```

### 3. 趋势强度计算

#### 双重因子模型：
```python
# 1. 一致性 (Consistency)
std_change = std(price_changes)  # 标准差
consistency = 1 - (std_change / (abs(avg_change) + 1))

# 2. 幅度 (Magnitude)  
magnitude = min(abs(avg_change) / 2, 1.0)

# 3. 综合强度
strength = consistency * 0.6 + magnitude * 0.4
```

#### 强度分级：
- **0.8-1.0**：强势（如连续大涨/大跌）
- **0.6-0.8**：中强（如稳步上涨/下跌）
- **0.4-0.6**：中等（如温和变化）
- **0.2-0.4**：偏弱（如小幅震荡）
- **0.0-0.2**：很弱（如横盘整理）

### 4. 成交量趋势

#### 判断逻辑：
```python
recent_avg = mean(volumes[-3:])    # 最近3天平均量
previous_avg = mean(volumes[-6:-3]) # 前3天平均量
change_ratio = (recent_avg - previous_avg) / previous_avg

if change_ratio > 15%:    # 放量
    volume_trend = "放量"
elif change_ratio < -15%: # 缩量  
    volume_trend = "缩量"
else:                     # 平稳
    volume_trend = "平稳"
```

#### 意义解读：
- **放量上涨**：资金积极入场，趋势可能持续
- **缩量上涨**：谨慎上涨，可能动能不足
- **放量下跌**：恐慌性抛售，可能见底
- **缩量下跌**：无量下跌，可能继续

### 5. 波动率计算

#### 算法：
```python
returns = [(prices[i] - prices[i-1]) / prices[i-1] 
           for i in range(1, len(prices))]
volatility = std(returns)  # 收益率标准差
```

#### 风险分级：
- **> 3%**：高波动（高风险）
- **2-3%**：中等波动（中等风险）
- **< 2%**：低波动（相对安全）

### 6. 风险水平评估

#### 综合评分体系：
```python
risk_score = 0

# 波动率风险 (0-30分)
if volatility > 3%: risk_score += 30
elif volatility > 2%: risk_score += 20
else: risk_score += 10

# 趋势风险 (0-30分)  
if trend == "下跌": risk_score += 30
elif trend == "震荡": risk_score += 20
else: risk_score += 10

# 强度风险 (0-20分)
if strength > 0.8: risk_score += 20  # 过强可能反转
elif strength < 0.3: risk_score += 15  # 过弱方向不明
else: risk_score += 5

# 最终评级
if risk_score > 60: return "高风险"
elif risk_score > 40: return "中等风险"  
else: return "低风险"
```

### 7. 多指数一致性

#### 综合判断：
```python
# 分析各个指数
sh_trend, sh_strength = analyze_index("上证指数")
sz_trend, sz_strength = analyze_index("深证成指") 
cy_trend, cy_strength = analyze_index("创业板指")

# 计算一致性
trends = [sh_trend, sz_trend, cy_trend]
main_trend = "上涨"  # 假设上证指数为上涨
consistency = count(trends == main_trend) / len(trends)

# 调整强度
adjusted_strength = sh_strength * consistency
```

#### 一致性影响：
- **90%以上**：市场共振，趋势可靠
- **60-90%**：多数一致，相对可靠
- **60%以下**：分化严重，需要谨慎

## 🔍 实际应用示例

### 示例1：强势上涨市场
```
分析结果：
• 趋势：上涨 (平均涨幅 +1.2%/天)
• 强度：0.85 (连续上涨，波动小)
• 成交量：放量 (+25%)
• 一致性：0.90 (三大指数同涨)
• 风险：中等

策略调整：
• 选股数量：3只 (增加)
• 评分门槛：15分 (降低)
• 策略：趋势跟随
```

### 示例2：弱势下跌市场
```
分析结果：
• 趋势：下跌 (平均跌幅 -0.8%/天)
• 强度：0.60 (持续下跌)
• 成交量：缩量 (-20%)
• 一致性：0.75 (多数下跌)
• 风险：高

策略调整：
• 选股数量：1只 (减少)
• 评分门槛：25分 (提高)  
• 策略：防守反击
```

### 示例3：震荡市场
```
分析结果：
• 趋势：震荡 (平均变化 +0.1%/天)
• 强度：0.30 (方向不明)
• 成交量：平稳 (+5%)
• 一致性：0.50 (分化严重)
• 风险：中等

策略调整：
• 选股数量：2只 (平衡)
• 评分门槛：22分 (适中)
• 策略：波段操作
```

## 🛠️ 测试和使用

### 查看实时分析：
```bash
# 运行市场分析
python3 scripts/real_market_analyzer.py

# 智能选股（自动应用市场分析）
./bot.sh smart
```

### 输出示例：
```
📊 市场状态摘要 (2025-07-21 10:30:15)

🎯 主要指标：
• 趋势方向：上涨
• 趋势强度：75% (强)
• 成交量：放量  
• 风险水平：中等
• 一致性：80%

🔥 热点板块：科技, 新能源, 医药

💡 市场解读：
• 强势上涨行情，可适度追涨
```

## ⚠️ 注意事项

1. **数据质量**：依赖准确的市场数据
2. **时效性**：市场变化快，需要实时更新
3. **辅助工具**：这是参考，不是绝对预测
4. **人工判断**：结合基本面和消息面分析
5. **风险控制**：再好的判断也要设置止损

## 🔄 持续优化

系统会根据实际效果不断优化：
- 调整权重参数
- 增加更多指标
- 优化算法逻辑
- 引入机器学习

这套市场强弱判断系统帮助您避免"与市场相反"的操作，提高选股成功率！
