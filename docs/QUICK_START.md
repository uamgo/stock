# A股尾盘交易系统 - 快速使用指南

## 系统介绍
A股尾盘交易系统是一个专业的股票交易策略工具，专门用于识别适合尾盘买入的股票。系统采用技术分析方法，结合量价关系、技术指标等多维度分析，为投资者提供决策支持。

## 快速开始

### 1. 系统启动
```bash
# 查看系统帮助
./tail_trading.py --help

# 查看版本信息
./tail_trading.py --version
```

### 2. 配置管理
```bash
# 查看可用配置
./tail_trading.py config --list

# 设置为保守型配置
./tail_trading.py config --preset conservative

# 显示当前配置
./tail_trading.py config --show
```

### 3. 选股操作
```bash
# 使用默认配置选股
./tail_trading.py select

# 使用保守型配置选股
./tail_trading.py select --preset conservative

# 限制显示前10只股票
./tail_trading.py select --limit 10

# 导出结果到CSV文件
./tail_trading.py select --output results.csv --format csv
```

### 4. 交易管理
```bash
# 进入交易管理模式
./tail_trading.py trade

# 查看交易帮助
./tail_trading.py trade --help
```

### 5. 持仓监控
```bash
# 监控当前持仓
./tail_trading.py monitor

# 查看历史交易记录
./tail_trading.py monitor --history
```

### 6. 数据更新
```bash
# 更新数据（默认top10板块）
./tail_trading.py update

# 更新top20板块数据
./tail_trading.py update --top-n 20

# 仅更新日线数据
./tail_trading.py update --daily-only

# 使用代理更新数据
./tail_trading.py update --use-proxy
```

## 配置说明

### 预设配置类型
- **conservative**: 保守型 - 低风险低收益
  - 较低的涨跌幅要求
  - 更严格的风险控制
  - 适合稳健投资者

- **balanced**: 平衡型 - 中风险中收益
  - 中等的涨跌幅要求
  - 平衡的风险收益
  - 适合普通投资者

- **aggressive**: 激进型 - 高风险高收益
  - 较高的涨跌幅要求
  - 更宽松的风险控制
  - 适合风险偏好投资者

### 主要参数说明
- `min_pct_chg`: 最小涨跌幅，过滤涨幅太小的股票
- `max_pct_chg`: 最大涨跌幅，过滤涨幅过大的股票
- `min_volume_ratio`: 最小量比，确保有足够的交易量
- `max_volume_ratio`: 最大量比，避免异常放量
- `min_prob_score`: 最小概率分数，确保成功概率
- `max_risk_score`: 最大风险分数，控制风险水平

## 策略说明

### 尾盘上涨策略
本系统主要使用尾盘上涨策略，该策略基于以下逻辑：
1. **技术分析**: 基于K线形态、均线位置等技术指标
2. **量价关系**: 分析成交量与价格的关系
3. **时间因素**: 重点关注尾盘时段的表现
4. **风险控制**: 多维度风险评估和控制

### 选股条件
- 涨跌幅在合理区间
- 量比适中，避免过度投机
- 技术形态良好
- 风险评分在可接受范围内

## 使用场景

### 日常选股
```bash
# 每日收盘后选股
./tail_trading.py select --preset balanced --limit 5

# 保存选股结果到文件
./tail_trading.py select --output daily_selection.txt
```

### 风险控制
```bash
# 使用保守配置降低风险
./tail_trading.py config --preset conservative
./tail_trading.py select
```

### 持仓管理
```bash
# 定期检查持仓状态
./tail_trading.py monitor

# 查看交易历史
./tail_trading.py monitor --history
```

## 输出格式

### 选股结果格式
```
【选股结果】
【排名 1】股票名称（股票代码）
  涨跌幅: 3.45%
  次日补涨概率: 75分
  风险评分: 35分
  量比: 2.3倍
  收盘价: 12.34元
  技术形态: 上涨趋势
  操作建议: 适合买入
```

### 监控结果格式
```
【持仓监控】
股票: 股票名称(000001)
  买入价格: 12.34元
  当前价格: 13.45元
  盈亏情况: +9.0%
  持有天数: 3天
  操作建议: 继续持有
```

## 注意事项

### 使用建议
1. **合理配置**: 根据个人风险承受能力选择合适的配置
2. **分散投资**: 不要集中买入单一股票
3. **及时止损**: 设定合理的止损点
4. **定期调整**: 根据市场情况调整策略参数

### 风险提示
1. 股票投资有风险，投资需谨慎
2. 本系统仅供参考，不构成投资建议
3. 请结合自己的判断进行投资决策
4. 注意控制仓位，合理分散风险

### 技术支持
如有问题，请查看：
- 项目说明文档
- 错误日志文件
- 配置文件设置

## 常见问题

### Q: 如何调整选股参数？
A: 使用配置命令调整参数，或者选择不同的预设配置。

### Q: 选股结果为空怎么办？
A: 可能是当前市场不符合策略条件，建议调整参数或等待更好的市场时机。

### Q: 如何理解概率分数和风险评分？
A: 概率分数越高表示成功可能性越大，风险评分越低表示风险越小。

### Q: 系统支持哪些股票市场？
A: 目前主要支持A股市场，数据来源于东方财富网。

---

更多详细信息请参考完整的项目文档和API参考。
