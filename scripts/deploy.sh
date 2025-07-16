#!/bin/bash

# A股尾盘交易系统 - 部署脚本
# 用于快速部署和初始化系统

set -e

echo "=== A股尾盘交易系统部署开始 ==="

# 检查Python版本
echo "📋 检查Python环境..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 检查是否有虚拟环境
if [ ! -d ".venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "📦 安装依赖包..."
pip install -r requirements.txt

# 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p config
mkdir -p data/cache
mkdir -p data/backtest
mkdir -p data/positions
mkdir -p logs

# 创建默认配置文件
echo "⚙️  创建默认配置..."
if [ ! -f "config/trading_config.json" ]; then
    python -c "
from tail_trading.config.trading_config import TradingConfig
config = TradingConfig()
config.save_config('config/trading_config.json')
print('默认配置文件已创建')
"
fi

# 给启动脚本添加执行权限
echo "🔐 设置文件权限..."
chmod +x tail_trading.py
chmod +x scripts/migrate.sh

# 测试系统
echo "🧪 测试系统..."
python tail_trading.py --version

echo "✅ 部署完成！"
echo ""
echo "快速开始："
echo "  ./tail_trading.py --help          # 查看帮助"
echo "  ./tail_trading.py config --list   # 查看配置"
echo "  ./tail_trading.py select          # 开始选股"
echo ""
echo "详细使用指南请查看 QUICK_START.md"
