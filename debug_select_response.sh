#!/bin/bash

echo "🔍 检查选股API返回的数据格式"
echo "=========================="

# 1. 登录
TOKEN=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "✅ 已获取token"

# 2. 调用选股API
echo "2. 调用选股API并分析响应结构..."
SELECT_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/select \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"preset":"balanced","limit":3,"verbose":false}')

echo "响应长度: ${#SELECT_RESPONSE} 字符"
echo ""

# 3. 分析响应结构
echo "=== 完整API响应 ==="
echo "$SELECT_RESPONSE"
echo ""

# 4. 尝试解析data字段
if echo "$SELECT_RESPONSE" | grep -q '"data"'; then
    echo "=== data字段内容 ==="
    # 简单提取data部分（注意：这是简化的提取，实际可能需要更复杂的解析）
    DATA_PART=$(echo "$SELECT_RESPONSE" | grep -o '"data":\[[^]]*\]' | sed 's/"data"://')
    echo "数据部分: $DATA_PART"
    
    if [ "$DATA_PART" = "[]" ]; then
        echo "❌ data字段为空数组"
    else
        echo "✅ data字段包含数据"
    fi
else
    echo "❌ 响应中没有data字段"
fi

echo ""
echo "=== 最新生成的文件内容 ==="
echo "选股结果文件:"
ls -la /tmp/selected_stocks*.txt 2>/dev/null | tail -1
echo "内容:"
ls -t /tmp/selected_stocks*.txt 2>/dev/null | head -1 | xargs cat 2>/dev/null
