# A股尾盘交易系统

一个专业的A股尾盘交易策略工具，采用技术分析方法，帮助投资者识别适合尾盘买入的股票。

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 基本使用
```bash
# 查看帮助
./tail_trading.py --help

# 选股操作
./tail_trading.py select

# 使用预设配置
./tail_trading.py select --preset conservative

# 配置管理
./tail_trading.py config --list
./tail_trading.py config --preset balanced

# 持仓监控
./tail_trading.py monitor

# 交易管理
./tail_trading.py trade
```

### 数据更新
```bash
# 更新数据
./tail_trading.py update

# 更新top20板块数据
./tail_trading.py update --top-n 20

# 仅更新日线数据
./tail_trading.py update --daily-only
```

## 📋 主要功能

### 1. 智能选股
- 基于技术分析的多维度筛选
- 支持自定义筛选条件
- 风险评估和概率评分

### 2. 配置管理
- 保守型、平衡型、激进型预设配置
- 灵活的参数调整
- 实时配置更新

### 3. 交易管理
- 完整的交易流程管理
- 持仓跟踪和监控
- 风险控制和止损

### 4. 数据分析
- 实时股票数据获取
- 技术指标计算
- 历史数据分析

### 5. 数据管理
- 自动化数据更新
- 支持top N板块选择
- 日线和分钟线数据同步

## 🏗️ 项目架构

```
tail_trading/
├── config/          # 配置管理
├── core/            # 核心业务逻辑
├── strategies/      # 交易策略
├── data/            # 数据层
└── cli/             # 命令行接口
```

## 📊 策略说明

### 尾盘上涨策略
- **选股条件**: 当日涨幅1-6%，量比适中
- **技术形态**: 下影线较长，上影线较短
- **时机把握**: 14:30-15:00尾盘时段
- **风险控制**: 多维度风险评估

### 最佳操作时机
- **周内**: 周一至周三最佳，周四可行，周五谨慎
- **日内**: 14:30-14:50黄金时段，14:50-15:00最后确认

## ⚙️ 配置选项

### 预设配置
- **conservative**: 保守型 - 低风险低收益
- **balanced**: 平衡型 - 中风险中收益  
- **aggressive**: 激进型 - 高风险高收益

### 主要参数
- `min_pct_chg`: 最小涨跌幅
- `max_pct_chg`: 最大涨跌幅
- `min_volume_ratio`: 最小量比
- `max_volume_ratio`: 最大量比
- `min_prob_score`: 最小概率分数
- `max_risk_score`: 最大风险分数

## 📚 文档

- [快速开始指南](QUICK_START.md)
- [项目重构报告](PROJECT_RESTRUCTURE_REPORT.md)
- [架构文档](docs/architecture.md)

## 🔧 部署

### 自动部署
```bash
./scripts/deploy.sh
```

### 手动部署
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建配置
mkdir -p config data/cache data/positions logs

# 测试系统
./tail_trading.py --version
```

## ⚠️ 风险提示

1. **投资风险**: 股票投资有风险，投资需谨慎
2. **仅供参考**: 本系统仅供参考，不构成投资建议
3. **理性投资**: 请结合自己的判断进行投资决策
4. **风险控制**: 注意控制仓位，合理分散风险

## 📜 版本历史

### 3.0.0 (当前版本)
- 完整重构为模块化架构
- 新增命令行界面
- 完善的配置管理系统
- 增强的风险管理功能

### 2.0.0 (旧版本)
- 实现多线程处理
- 执行耗时 36.44s

### 1.0.0 (旧版本)
- 单线程版本
- 执行耗时 146.77s

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests 来改进这个项目。

## 📄 许可证

本项目采用 MIT 许可证。
