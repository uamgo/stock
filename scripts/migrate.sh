#!/bin/bash
# 系统迁移脚本
# 将原有的legacy代码迁移到新的项目结构

echo "=== A股尾盘交易系统迁移脚本 ==="
echo "正在将原有代码迁移到新的项目结构..."

# 项目根目录
PROJECT_ROOT="/Users/kevin/workspace/stock"
LEGACY_DIR="$PROJECT_ROOT/legacy"

# 创建legacy目录
mkdir -p "$LEGACY_DIR"

# 迁移原有的policies代码
echo "1. 迁移策略文件..."
if [ -d "$PROJECT_ROOT/data/est/policies" ]; then
    cp -r "$PROJECT_ROOT/data/est/policies" "$LEGACY_DIR/old_policies"
    echo "   ✅ 策略文件已迁移到 $LEGACY_DIR/old_policies"
else
    echo "   ⚠️  策略目录不存在，跳过"
fi

# 迁移原有的data目录
echo "2. 迁移数据模块..."
if [ -d "$PROJECT_ROOT/data" ]; then
    cp -r "$PROJECT_ROOT/data" "$LEGACY_DIR/old_data"
    echo "   ✅ 数据模块已迁移到 $LEGACY_DIR/old_data"
else
    echo "   ⚠️  数据目录不存在，跳过"
fi

# 迁移其他遗留文件
echo "3. 迁移其他遗留文件..."
legacy_files=(
    "tail_trading.py"
    "tail_trading.sh"
    "chat_impl.py"
    "selected_codes.txt"
)

for file in "${legacy_files[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        cp "$PROJECT_ROOT/$file" "$LEGACY_DIR/"
        echo "   ✅ $file 已迁移"
    else
        echo "   ⚠️  $file 不存在，跳过"
    fi
done

# 更新README
echo "4. 更新项目文档..."
if [ -f "$PROJECT_ROOT/README_NEW.md" ]; then
    cp "$PROJECT_ROOT/README.md" "$LEGACY_DIR/README_OLD.md"
    mv "$PROJECT_ROOT/README_NEW.md" "$PROJECT_ROOT/README.md"
    echo "   ✅ README已更新"
fi

# 创建新的启动脚本
echo "5. 创建新的启动脚本..."
cat > "$PROJECT_ROOT/start_tail_trading.sh" << 'EOF'
#!/bin/bash
# 尾盘交易系统启动脚本

cd "$(dirname "$0")"

echo "=== 尾盘交易系统启动 ==="
echo "时间: $(date)"
echo

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: Python未安装或不在PATH中"
    exit 1
fi

# 检查依赖
if ! python -c "import pandas, akshare" 2>/dev/null; then
    echo "安装依赖包..."
    pip install -r requirements.txt
fi

# 显示使用帮助
echo "使用方法:"
echo "  python -m tail_trading.cli.main select    # 选股"
echo "  python -m tail_trading.cli.main trade     # 交易管理"
echo "  python -m tail_trading.cli.main monitor   # 监控持仓"
echo "  python -m tail_trading.cli.main config    # 配置管理"
echo

# 如果有参数，直接执行
if [ $# -gt 0 ]; then
    python -m tail_trading.cli.main "$@"
else
    # 默认运行选股
    python -m tail_trading.cli.main select
fi
EOF

chmod +x "$PROJECT_ROOT/start_tail_trading.sh"
echo "   ✅ 启动脚本已创建"

# 创建安装脚本
echo "6. 创建安装脚本..."
cat > "$PROJECT_ROOT/install.sh" << 'EOF'
#!/bin/bash
# 尾盘交易系统安装脚本

cd "$(dirname "$0")"

echo "=== 尾盘交易系统安装 ==="

# 检查Python版本
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 安装依赖
echo "安装Python依赖包..."
pip install -r requirements.txt

# 创建必要目录
echo "创建系统目录..."
mkdir -p logs data/cache data/exports data/backups

# 设置权限
echo "设置文件权限..."
chmod +x start_tail_trading.sh

echo "✅ 安装完成！"
echo
echo "使用方法:"
echo "  ./start_tail_trading.sh select    # 选股"
echo "  ./start_tail_trading.sh trade     # 交易管理"
echo "  ./start_tail_trading.sh monitor   # 监控持仓"
echo "  ./start_tail_trading.sh config    # 配置管理"
EOF

chmod +x "$PROJECT_ROOT/install.sh"
echo "   ✅ 安装脚本已创建"

# 创建gitignore
echo "7. 更新.gitignore..."
cat > "$PROJECT_ROOT/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# 项目特定
logs/
data/cache/
data/exports/
data/backups/
*.log
.env

# 配置文件
.tail_trading_config.json
.tail_trading_positions.json
.tail_trading_trades.json

# 临时文件
*.tmp
*.bak
selected_codes.txt
up_up_data.txt
up_up_report.txt
EOF

echo "   ✅ .gitignore已更新"

echo
echo "🎉 迁移完成！"
echo
echo "新的项目结构:"
echo "  📁 tail_trading/          # 核心交易系统"
echo "  📁 tests/                 # 测试代码"
echo "  📁 docs/                  # 文档"
echo "  📁 scripts/               # 脚本"
echo "  📁 legacy/                # 遗留代码"
echo
echo "快速开始:"
echo "  1. 运行安装脚本: ./install.sh"
echo "  2. 开始选股: ./start_tail_trading.sh select"
echo "  3. 查看帮助: ./start_tail_trading.sh --help"
echo
echo "原有代码已保存在 legacy/ 目录中"
EOF
