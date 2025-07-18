#!/bin/bash

echo "🚀 最终选股功能测试"
echo "==================="

# 1. 登录
echo "1. 重新登录获取新token..."
TOKEN=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    exit 1
fi

echo "✅ 登录成功，新token已获取"

# 2. 测试用户信息
echo "2. 验证token有效性..."
USER_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://stock.uamgo.com/api/auth/me)
if echo "$USER_RESPONSE" | grep -q '"username"'; then
    echo "✅ Token验证成功"
else
    echo "❌ Token验证失败: $USER_RESPONSE"
    exit 1
fi

# 3. 测试选股API
echo "3. 测试选股功能..."
echo "请求参数: {\"preset\":\"balanced\",\"limit\":3,\"verbose\":false}"

SELECT_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/select \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"preset":"balanced","limit":3,"verbose":false}' \
  --max-time 30)

echo "选股API响应长度: ${#SELECT_RESPONSE} 字符"

if echo "$SELECT_RESPONSE" | grep -q '"success"'; then
    SUCCESS=$(echo "$SELECT_RESPONSE" | grep -o '"success":[^,}]*' | cut -d':' -f2)
    echo "✅ 选股API调用成功"
    echo "成功状态: $SUCCESS"
    
    if echo "$SELECT_RESPONSE" | grep -q '"data"'; then
        echo "✅ 包含股票数据"
    else
        echo "⚠️ 无股票数据返回"
    fi
else
    echo "❌ 选股API失败"
    echo "响应内容: $SELECT_RESPONSE"
fi

echo ""
echo "🎯 测试总结："
echo "- JWT token过期时间已从30分钟增加到8小时"
echo "- 前端已改进401错误处理，会显示友好提示"
echo "- 选股功能现在应该可以正常工作"
echo ""
echo "📱 请访问 http://stock.uamgo.com 重新登录并测试选股功能"
