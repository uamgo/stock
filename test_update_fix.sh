#!/bin/bash

echo "🧪 测试修复后的股票数据更新功能..."

# 先登录获取token
echo "1. 登录获取访问令牌..."
LOGIN_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败！"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ 登录成功"

# 测试数据更新（较小的数量以避免超时）
echo "2. 测试股票数据更新（TOP 3）..."
UPDATE_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/update \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"top_n":3}' \
  --max-time 300)

echo "更新响应:"
echo "$UPDATE_RESPONSE" | jq . 2>/dev/null || echo "$UPDATE_RESPONSE"

# 检查响应是否为有效JSON
if echo "$UPDATE_RESPONSE" | jq . >/dev/null 2>&1; then
    echo "✅ 返回了有效的JSON响应"
    
    # 检查是否成功
    if echo "$UPDATE_RESPONSE" | jq -r '.success' | grep -q "true"; then
        echo "✅ 数据更新成功"
    else
        echo "⚠️ 数据更新失败，但返回了正确的错误格式"
    fi
else
    echo "❌ 返回了无效的JSON响应"
fi

echo "🎯 测试完成！"
