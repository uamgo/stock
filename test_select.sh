#!/bin/bash

echo "🔧 测试选股API鉴权..."

# 获取token
echo "获取新token..."
LOGIN_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin000"}')

echo "登录响应: $LOGIN_RESPONSE"

if echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "✅ Token获取成功: ${TOKEN:0:20}..."
else
    echo "❌ 登录失败"
    exit 1
fi

# 测试用户信息接口
echo ""
echo "测试用户信息接口..."
USER_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://stock.uamgo.com/api/user/me")
echo "用户信息响应: $USER_RESPONSE"

# 测试选股接口
echo ""
echo "测试选股接口..."
SELECT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"preset":"概念热度","limit":5,"verbose":false}' \
  "http://stock.uamgo.com/api/stock/select")

echo "选股响应长度: ${#SELECT_RESPONSE} 字符"
echo "选股响应前200字符:"
echo "$SELECT_RESPONSE" | head -c 200
echo ""

if echo "$SELECT_RESPONSE" | grep -q "Invalid authentication credentials"; then
    echo "❌ 鉴权失败"
elif echo "$SELECT_RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    echo "✅ 选股API返回有效JSON"
else
    echo "❌ 选股API返回无效响应"
fi
