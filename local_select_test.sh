#!/bin/bash

echo "🔧 本地测试选股API"
echo "================"

# 测试登录
echo "1. 测试登录..."
TOKEN=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    exit 1
fi

echo "✅ 登录成功"

# 测试选股
echo "2. 测试选股API..."
RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/select \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"preset":"balanced","limit":2,"verbose":false}' \
  --max-time 60)

echo "响应长度: ${#RESPONSE} 字符"

# 分析响应
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ API调用成功"
    
    if echo "$RESPONSE" | grep -q '"data":\['; then
        echo "✅ 包含data字段"
        if echo "$RESPONSE" | grep -q '"data":\[\]'; then
            echo "❌ data数组为空"
            echo "完整响应:"
            echo "$RESPONSE"
        else
            echo "✅ data数组包含数据"
            # 提取股票数量
            STOCK_COUNT=$(echo "$RESPONSE" | grep -o '"代码"' | wc -l)
            echo "股票数量: $STOCK_COUNT"
        fi
    else
        echo "❌ 缺少data字段"
    fi
else
    echo "❌ API调用失败"
    echo "响应: $RESPONSE"
fi
