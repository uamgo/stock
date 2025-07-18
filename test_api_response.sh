#!/bin/bash

echo "🔍 API响应格式检查..."

# 1. 测试登录API
echo "1. 测试登录API响应格式..."
LOGIN_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}')

echo "登录响应完整内容:"
echo "$LOGIN_RESPONSE" | tr -d '\0'
echo ""
echo "登录响应长度: ${#LOGIN_RESPONSE} 字符"

# 检查是否为有效JSON
if echo "$LOGIN_RESPONSE" | jq . >/dev/null 2>&1; then
    echo "✅ 登录API返回有效JSON"
    TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
else
    echo "❌ 登录API返回无效JSON"
    exit 1
fi

# 2. 测试健康检查API
echo "2. 测试健康检查API..."
HEALTH_RESPONSE=$(curl -s http://stock.uamgo.com/api/health)
echo "健康检查响应: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | jq . >/dev/null 2>&1; then
    echo "✅ 健康检查API返回有效JSON"
else
    echo "❌ 健康检查API返回无效JSON"
fi

# 3. 测试股票更新API（快速超时测试）
echo "3. 测试股票更新API（3秒超时）..."
UPDATE_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/update \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"top_n":1}' \
  --max-time 3)

echo "更新API响应长度: ${#UPDATE_RESPONSE} 字符"
echo "更新API响应前100字符:"
echo "$UPDATE_RESPONSE" | head -c 100
echo ""

# 检查响应类型
if echo "$UPDATE_RESPONSE" | grep -q "^<html"; then
    echo "❌ 返回了HTML页面而不是JSON"
    echo "可能是nginx返回的错误页面"
elif echo "$UPDATE_RESPONSE" | jq . >/dev/null 2>&1; then
    echo "✅ 返回了有效的JSON"
    SUCCESS=$(echo "$UPDATE_RESPONSE" | jq -r '.success')
    MESSAGE=$(echo "$UPDATE_RESPONSE" | jq -r '.message')
    echo "成功状态: $SUCCESS"
    echo "消息: $MESSAGE"
else
    echo "❌ 返回了无效的JSON"
fi

echo ""
echo "🎯 建议："
echo "如果看到HTML响应，说明请求可能被nginx拦截或超时"
echo "如果看到JSON错误，说明后端处理有问题"
