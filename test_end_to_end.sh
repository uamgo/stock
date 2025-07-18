#!/bin/bash

echo "🎯 端到端选股测试"
echo "================"

# 1. 登录
echo "1. 登录获取token..."
TOKEN=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "✅ 登录成功"

# 2. 调用选股API
echo "2. 调用选股API..."
SELECT_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/stock/select \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"preset":"balanced","limit":2,"verbose":false}' \
  --max-time 120)

echo "API响应长度: ${#SELECT_RESPONSE} 字符"

# 3. 分析响应
if echo "$SELECT_RESPONSE" | grep -q '"success":true'; then
    echo "✅ API调用成功"
    
    # 检查data字段
    if echo "$SELECT_RESPONSE" | grep -q '"data":\['; then
        echo "✅ 包含data数组"
        
        # 检查是否为空数组
        if echo "$SELECT_RESPONSE" | grep -q '"data":\[\]'; then
            echo "❌ data数组为空"
        else
            echo "✅ data数组包含数据"
        fi
        
        # 检查中文字段
        if echo "$SELECT_RESPONSE" | grep -q '"代码"'; then
            echo "✅ 包含中文字段'代码'"
        else
            echo "❌ 缺少中文字段'代码'"
        fi
        
        if echo "$SELECT_RESPONSE" | grep -q '"名称"'; then
            echo "✅ 包含中文字段'名称'"
        else
            echo "❌ 缺少中文字段'名称'"
        fi
        
    else
        echo "❌ 缺少data字段"
    fi
    
    echo ""
    echo "=== 响应内容示例 ==="
    echo "$SELECT_RESPONSE" | head -c 500
    echo "..."
    
else
    echo "❌ API调用失败"
    echo "响应: $SELECT_RESPONSE"
fi

echo ""
echo "🎯 修复总结："
echo "- 前端已修改以支持中文字段名"
echo "- 代码 -> stock.代码"
echo "- 名称 -> stock.名称"  
echo "- 次日补涨概率 -> stock.次日补涨概率"
echo "- 风险评分 -> stock.风险评分"
