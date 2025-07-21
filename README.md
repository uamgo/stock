# 股票数据分析系统

一个基于 Python + React 的股票数据分析和展示系统。

## 项目结构

```
├── backend/            # 后端 Python 代码
├── frontend/           # 前端 React 代码
├── scripts/            # 各类脚本
│   ├── deployment/     # 部署相关脚本
│   ├── development/    # 开发环境脚本
│   ├── testing/        # 测试脚本
│   └── maintenance/    # 维护脚本
├── config/             # 配置文件
├── docs/               # 项目文档
│   ├── deployment/     # 部署相关文档
│   └── reports/        # 各种报告文档
├── data/               # 数据目录
├── logs/               # 日志目录
└── tests/              # 单元测试
```

## 快速开始

### 🤖 智能选股（推荐）

**解决选股与市场相反的问题**：
```bash
# 市场适应性智能选股
./bot.sh smart
```

特点：
- 🎯 根据市场环境自动调整策略
- 📊 避免与市场趋势相反的操作
- 🛡️ 智能风险控制和仓位分配
- 💡 提供具体的操作建议

### 开发环境

1. 安装依赖：
   ```bash
   ./scripts/development/install_deps.sh
   ```

2. 启动开发服务器：
   ```bash
   ./scripts/development/start_dev.sh
   ```

### 部署

1. 本地部署（推荐）：
   ```bash
   ./bot.sh deploy
   ```

2. 使用管理工具：
   ```bash
   ./bot.sh setup
   ```

### 选股分析

1. **智能选股（推荐）**：
   ```bash
   ./bot.sh smart
   ```

2. **传统选股**：
   ```bash
   ./bot.sh select
   ```

3. **使用管理工具**：
   ```bash
   ./bot.sh test
   ```

## 文档

- [快速开始指南](docs/QUICK_START.md)
- [部署指南](docs/deployment/)
- [故障排除指南](docs/TROUBLESHOOTING_GUIDE.md)

## 维护

- 检查系统状态：`./scripts/maintenance/check_status.sh`
- 系统诊断：`./scripts/maintenance/diagnose.sh`
