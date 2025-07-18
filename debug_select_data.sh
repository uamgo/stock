#!/bin/bash

echo "🔍 调试选股API数据返回"
echo "====================="

# 1. 登录获取token
TOKEN=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "✅ 已获取token"

# 2. 调用选股API
echo "2. 调用选股API..."
SELECT_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/select \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"preset":"balanced","limit":3,"verbose":false}' \
  --max-time 60)

echo "API响应长度: ${#SELECT_RESPONSE} 字符"

# 3. 分析响应结构
echo ""
echo "=== 完整API响应 ==="
echo "$SELECT_RESPONSE" | head -c 1000
echo ""

# 4. 检查关键字段
echo "=== 字段检查 ==="
if echo "$SELECT_RESPONSE" | grep -q '"success":true'; then
    echo "✅ success字段为true"
else
    echo "❌ success字段不为true"
fi

if echo "$SELECT_RESPONSE" | grep -q '"data":\['; then
    echo "✅ 包含data数组"
    
    # 检查data是否为空
    if echo "$SELECT_RESPONSE" | grep -q '"data":\[\]'; then
        echo "❌ data数组为空"
    else
        echo "✅ data数组包含数据"
        
        # 尝试提取第一个股票数据
        echo ""
        echo "=== 股票数据示例 ==="
        echo "$SELECT_RESPONSE" | grep -o '"data":\[[^]]*\]' | head -c 500
        echo ""
    fi
else
    echo "❌ 缺少data字段"
fi

# 5. 检查中文字段
echo ""
echo "=== 中文字段检查 ==="
if echo "$SELECT_RESPONSE" | grep -q '"代码"'; then
    echo "✅ 包含'代码'字段"
else
    echo "❌ 缺少'代码'字段"
fi

if echo "$SELECT_RESPONSE" | grep -q '"名称"'; then
    echo "✅ 包含'名称'字段"
else
    echo "❌ 缺少'名称'字段"
fi
