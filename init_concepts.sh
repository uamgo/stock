#!/bin/bash

echo "🚀 初始化概念板块数据..."

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

# 调用概念数据初始化API
echo "2. 开始初始化概念数据（这可能需要几分钟）..."
curl -X POST http://stock.uamgo.com/api/stock/init-concepts \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  --max-time 1800

echo -e "\n🎯 初始化完成！"
