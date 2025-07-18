#!/bin/bash

echo "🔍 选股API认证详细调试"
echo "========================"

# 1. 登录获取token
echo "1. 登录获取token..."
LOGIN_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}')

echo "登录响应: $LOGIN_RESPONSE"

# 提取token
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
echo "提取的Token: $TOKEN"

if [ -z "$TOKEN" ]; then
    echo "❌ Token提取失败"
    exit 1
fi

echo ""
echo "2. 测试选股API认证..."

# 显示完整的curl命令
echo "执行的curl命令:"
echo "curl -v -X POST http://stock.uamgo.com/api/stock/select \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'Authorization: Bearer $TOKEN' \\"
echo "  -d '{\"preset\":\"balanced\",\"limit\":3,\"verbose\":false}'"
echo ""

# 执行选股API调用
echo "API响应:"
curl -v -X POST http://stock.uamgo.com/api/stock/select \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"preset":"balanced","limit":3,"verbose":false}' \
  2>&1

echo ""
echo "3. 验证token是否有效..."
USER_INFO=$(curl -s -H "Authorization: Bearer $TOKEN" http://stock.uamgo.com/api/auth/me)
echo "用户信息响应: $USER_INFO"

if echo "$USER_INFO" | grep -q '"username"'; then
    echo "✅ Token有效"
else
    echo "❌ Token无效"
fi
