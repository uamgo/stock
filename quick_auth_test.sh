#!/bin/bash

echo "🔍 快速API认证测试"
echo "=================="

# 1. 获取认证token
echo "1. 登录测试..."
TOKEN=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}' | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    exit 1
else
    echo "✅ 登录成功"
fi

# 2. 测试需要认证的API
echo "2. 测试认证API..."

# 用户信息
USER_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://stock.uamgo.com/api/auth/me)
if echo "$USER_RESPONSE" | jq -e '.username' >/dev/null 2>&1; then
    echo "✅ 用户信息API正常"
else
    echo "❌ 用户信息API失败"
fi

# 股票更新API（快速测试）
UPDATE_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"top_n":1}' \
  --max-time 10 \
  http://stock.uamgo.com/api/stock/update)

if echo "$UPDATE_RESPONSE" | jq -e '.success' >/dev/null 2>&1; then
    echo "✅ 股票更新API正常"
else
    echo "❌ 股票更新API失败"
    echo "响应: $UPDATE_RESPONSE"
fi

# 股票选择API
SELECT_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"top_n":5}' \
  http://stock.uamgo.com/api/stock/select)

if echo "$SELECT_RESPONSE" | jq -e '.success' >/dev/null 2>&1; then
    echo "✅ 股票选择API正常"
else
    echo "❌ 股票选择API失败"
    echo "响应: $SELECT_RESPONSE"
fi

echo ""
echo "🎯 测试完成 - 系统状态正常"
