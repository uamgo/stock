#!/bin/bash

echo "🔧 选股输出路径修复测试"
echo "========================"

# 1. 登录获取token
echo "1. 获取认证token..."
TOKEN=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    exit 1
fi

echo "✅ 登录成功"

# 2. 测试选股功能
echo "2. 测试选股功能..."
echo "调用参数: {\"preset\":\"balanced\",\"limit\":3,\"verbose\":false}"

SELECT_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/select \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"preset":"balanced","limit":3,"verbose":false}' \
  --max-time 60)

echo "选股响应长度: ${#SELECT_RESPONSE} 字符"

# 检查响应内容
if echo "$SELECT_RESPONSE" | grep -q '"success":true'; then
    echo "✅ 选股成功！"
    
    # 显示部分响应内容
    echo "响应摘要:"
    echo "$SELECT_RESPONSE" | head -c 500
    echo "..."
    
    # 检查是否有数据
    if echo "$SELECT_RESPONSE" | grep -q '"data"'; then
        echo "✅ 包含股票数据"
    else
        echo "⚠️ 无股票数据"
    fi
    
elif echo "$SELECT_RESPONSE" | grep -q '"success":false'; then
    echo "❌ 选股失败"
    MESSAGE=$(echo "$SELECT_RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
    echo "错误信息: $MESSAGE"
    
elif echo "$SELECT_RESPONSE" | grep -q "No such file or directory"; then
    echo "❌ 仍然存在文件路径问题"
    echo "错误详情: $SELECT_RESPONSE"
    
else
    echo "❓ 未知响应格式"
    echo "完整响应: $SELECT_RESPONSE"
fi

echo ""
echo "3. 检查服务器/tmp目录..."
ssh root@login.uamgo.com 'ls -la /tmp/selected_stocks*.txt 2>/dev/null || echo "暂无输出文件"'

echo ""
echo "🎯 测试完成！"
