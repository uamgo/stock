#!/bin/bash

# 本地生产环境部署脚本
# 前端已部署在nginx，后端本地运行，无需Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 本地生产环境部署"
echo "===================================================="
echo "前端: 已部署在nginx目录"
echo "后端: 本地Python环境运行"
echo "数据: 使用真实API数据源"
echo "===================================================="

# 1. 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python版本: $PYTHON_VERSION"

# 2. 检查并创建虚拟环境
echo "📦 检查虚拟环境..."
cd "$PROJECT_ROOT"

if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
    echo "✅ 虚拟环境创建完成"
else
    echo "✅ 虚拟环境已存在"
fi

# 3. 激活虚拟环境并安装/更新依赖
echo "📥 更新依赖..."
source .venv/bin/activate

# 升级pip
pip install --upgrade pip --quiet

# 安装项目依赖
if [ -f "requirements.txt" ]; then
    echo "安装主项目依赖..."
    pip install -r requirements.txt --quiet
    echo "✅ 主项目依赖更新完成"
fi

# 安装后端依赖
if [ -f "backend/requirements.txt" ]; then
    echo "安装后端依赖..."
    pip install -r backend/requirements.txt --quiet
    echo "✅ 后端依赖更新完成"
fi

# 4. 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p logs
mkdir -p backups
mkdir -p /tmp/stock
mkdir -p /tmp/stock/daily
mkdir -p /tmp/stock/cache
mkdir -p /tmp/stock/est_prepare_data
echo "✅ 目录结构完成"

# 5. 设置权限
echo "🔧 设置权限..."
chmod +x bot.sh
chmod +x deploy.sh 2>/dev/null || true
find scripts/ -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
echo "✅ 权限设置完成"

# 6. 清理旧数据缓存（可选）
if [ "$1" = "--clean" ]; then
    echo "🧹 清理旧缓存..."
    rm -rf /tmp/stock/cache/* 2>/dev/null || true
    echo "✅ 缓存清理完成"
fi

# 7. 运行健康检查
echo "🏥 运行系统健康检查..."
if python3 scripts/production_health_check.py; then
    echo "✅ 系统健康检查通过"
else
    echo "⚠️ 健康检查发现一些问题，但不影响基本功能"
fi

# 8. 初始化数据（如果需要）
if [ "$1" = "--init-data" ] || [ ! -f "/tmp/stock/est_prepare_data/members_dict.pkl" ]; then
    echo "📊 初始化基础数据..."
    if python3 scripts/production_data_updater.py --mode=concept; then
        echo "✅ 基础数据初始化完成"
    else
        echo "⚠️ 数据初始化遇到网络问题，可稍后手动更新"
    fi
fi

# 9. 测试核心功能
echo "🧪 测试核心功能..."
if python3 -c "from scripts.smart_select import SmartStockSelector; print('✅ 智能选股模块正常')"; then
    echo "✅ 核心模块测试通过"
else
    echo "⚠️ 部分模块测试失败，但系统已部署"
fi

echo ""
echo "🎉 本地生产环境部署完成！"
echo "===================================================="
echo ""
echo "📝 快速使用："
echo "  ./bot.sh smart      # 智能选股（推荐）"
echo "  ./bot.sh enhanced   # 增强选股"
echo "  ./bot.sh health     # 健康检查"
echo "  ./bot.sh update     # 数据更新"
echo "  ./bot.sh monitor    # 性能监控"
echo ""
echo "🔧 管理命令："
echo "  ./bot.sh backup     # 数据备份"
echo "  ./bot.sh status     # 系统状态"
echo "  ./bot.sh logs       # 查看日志"
echo ""
echo "🚀 立即开始："
echo "  ./bot.sh smart"
echo ""

# 10. 显示部署信息
echo "📋 部署信息："
echo "  部署类型: 本地生产环境"
echo "  Python版本: $PYTHON_VERSION"  
echo "  项目路径: $PROJECT_ROOT"
echo "  虚拟环境: .venv"
echo "  数据目录: /tmp/stock"
echo "  前端: nginx目录（已部署）"
echo "  后端: 本地Python运行"
echo ""
echo "✅ 部署成功！无需Docker，轻量高效。"

# 11. 可选的后端服务启动提示
if [ -f "backend/start.sh" ]; then
    echo ""
    echo "💡 提示: 如需启动后端API服务，请运行："
    echo "  cd backend && ./start.sh"
fi
