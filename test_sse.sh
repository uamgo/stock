#!/bin/bash

echo "🔧 测试SSE流式API..."

# 获取token
TOKEN=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin000"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token获取成功: ${TOKEN:0:20}..."

# 测试SSE接口
echo "测试SSE接口（5秒超时）："
timeout 5 curl -s -H "Authorization: Bearer $TOKEN" \
  "http://stock.uamgo.com/api/stock/update-stream?top_n=1" | head -5

echo ""
echo "测试完成"
