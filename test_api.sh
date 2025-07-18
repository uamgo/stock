#!/bin/bash

echo "🧪 测试股票数据更新功能..."

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

echo "✅ 登录成功，获取到访问令牌"

# 测试数据更新
echo "2. 测试股票数据更新..."
UPDATE_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/update \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"top_n":5}')

echo "更新响应:"
echo $UPDATE_RESPONSE | jq . 2>/dev/null || echo $UPDATE_RESPONSE

# 测试股票查询
echo "3. 测试股票查询..."
QUERY_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/select \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"limit":3,"format":"json"}')

echo "查询响应:"
echo $QUERY_RESPONSE | jq . 2>/dev/null || echo $QUERY_RESPONSE

echo "🎯 测试完成！"
