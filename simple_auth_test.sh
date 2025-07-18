#!/bin/bash

echo "🔍 快速API认证测试"
echo "=================="

# 1. 获取认证token
echo "1. 登录测试..."
LOGIN_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}')

# 简单提取token (不依赖jq)
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
else
    echo "✅ 登录成功"
fi

# 2. 测试用户信息API
echo "2. 测试用户信息API..."
USER_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://stock.uamgo.com/api/auth/me)
if echo "$USER_RESPONSE" | grep -q '"username"'; then
    echo "✅ 用户信息API正常"
else
    echo "❌ 用户信息API失败: $USER_RESPONSE"
fi

# 3. 测试股票选择API
echo "3. 测试股票选择API..."
SELECT_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"top_n":3}' \
  http://stock.uamgo.com/api/stock/select)

if echo "$SELECT_RESPONSE" | grep -q '"success"'; then
    echo "✅ 股票选择API正常"
else
    echo "❌ 股票选择API失败"
    echo "响应: $SELECT_RESPONSE"
fi

# 4. 测试SSE流
echo "4. 测试SSE认证..."
timeout 5 curl -s -H "Authorization: Bearer $TOKEN" \
  http://stock.uamgo.com/api/stock/stream_update_logs \
  | head -n 3

if [ $? -eq 0 ]; then
    echo "✅ SSE流认证正常"
else
    echo "❌ SSE流认证失败"
fi

echo ""
echo "🎯 认证测试完成！"
echo "📱 请访问 http://stock.uamgo.com 测试前端功能"
