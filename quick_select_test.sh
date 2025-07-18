#!/bin/bash

echo "🔧 快速选股API测试"
echo "================"

# 登录
TOKEN=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "✅ 已登录"

# 快速选股测试
echo "开始选股..."
RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/select \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"preset":"balanced","limit":2,"verbose":false}' \
  --max-time 30)

echo "响应长度: ${#RESPONSE}"

# 检查关键字段
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ 成功"
else
    echo "❌ 失败"
fi

if echo "$RESPONSE" | grep -q '"data":\['; then
    echo "✅ 有data字段"
    if echo "$RESPONSE" | grep -q '"data":\[\]'; then
        echo "❌ data为空"
    else
        echo "✅ data有内容"
    fi
else
    echo "❌ 无data字段"
fi

# 显示响应前500字符
echo ""
echo "=== 响应内容 ==="
echo "$RESPONSE" | head -c 500
