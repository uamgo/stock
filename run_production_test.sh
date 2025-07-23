#!/bin/bash
# 生产环境热度测试执行脚本

echo "🚀 开始生产环境热度测试..."
echo "📍 连接到生产服务器: stock.uamgo.com"

ssh root@stock.uamgo.com << 'EOF'
cd /home/uamgo/stock
echo "📍 当前目录: $(pwd)"
echo "📍 使用Python环境: .venv/bin/python"

# 运行测试脚本
.venv/bin/python production_test.py

echo "✅ 测试完成"
EOF

echo "🏁 生产环境测试结束"
