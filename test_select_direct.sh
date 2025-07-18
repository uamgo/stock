#!/bin/bash

echo "🔧 测试选股脚本直接输出"
echo "======================"

cd /home/uamgo/stock

echo "1. 直接运行选股脚本（JSON格式）..."
echo "命令: python3 tail_trading.py select --preset balanced --limit 2 --format json"

# 运行选股脚本并获取输出
OUTPUT=$(/home/uamgo/stock/venv/bin/python3 tail_trading.py select --preset balanced --limit 2 --format json 2>&1)

echo "脚本完整输出:"
echo "============="
echo "$OUTPUT"
echo "============="
echo ""

# 尝试提取JSON部分
echo "2. 分析输出格式..."
if echo "$OUTPUT" | grep -q '^\['; then
    echo "✅ 输出以JSON数组开始"
    JSON_PART=$(echo "$OUTPUT" | grep '^\[' | head -1)
    echo "JSON部分: $JSON_PART"
elif echo "$OUTPUT" | grep -q '  {'; then
    echo "✅ 输出包含JSON对象"
    echo "需要提取JSON部分..."
else
    echo "❌ 输出不是JSON格式"
fi

echo ""
echo "3. 检查生成的文件..."
ls -la /tmp/selected_stocks*.txt 2>/dev/null | tail -1
