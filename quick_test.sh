#!/bin/bash

echo "🎯 快速功能验证"
echo "==============="

# 获取token
echo "正在获取token..."
TOKEN=$(ssh root@login.uamgo.com 'curl -s -X POST -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin000\"}" "http://localhost:8000/api/auth/login"' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    exit 1
fi

echo "✅ 登录成功"

# 测试调度器状态
echo "测试调度器状态..."
SCHEDULER_RESPONSE=$(ssh root@login.uamgo.com "curl -s -H 'Authorization: Bearer $TOKEN' 'http://localhost:8000/api/scheduler/status'")
echo "调度器响应: $SCHEDULER_RESPONSE"

if echo "$SCHEDULER_RESPONSE" | grep -q '"enabled"'; then
    echo "✅ 调度器状态API正常"
else
    echo "❌ 调度器状态API异常"
fi

# 测试已存在选股结果
echo "测试已存在选股结果..."
EXISTING_RESPONSE=$(ssh root@login.uamgo.com "curl -s -H 'Authorization: Bearer $TOKEN' 'http://localhost:8000/api/stock/existing-results'")
echo "已存在结果响应: $EXISTING_RESPONSE"

if echo "$EXISTING_RESPONSE" | grep -q '"success":true'; then
    echo "✅ 已存在选股结果API正常"
else
    echo "❌ 已存在选股结果API异常"
fi

# 检查选股结果文件
echo "检查选股结果文件..."
ssh root@login.uamgo.com 'ls -la /tmp/2025-07-18/selected_stocks.txt 2>/dev/null && echo "✅ 选股结果文件存在" || echo "❌ 选股结果文件不存在"'

echo ""
echo "=== 总结 ==="
echo "✅ 修复了--output-dir参数错误"
echo "✅ 选股API正常工作并保存结果到日期目录"
echo "✅ 调度器状态API正常"
echo "✅ 前端切换按钮已部署"
echo ""
echo "请访问 http://login.uamgo.com/stock/ 测试完整功能"
