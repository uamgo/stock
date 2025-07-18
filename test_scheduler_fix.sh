#!/bin/bash

echo "🔧 测试定时任务状态修复"
echo "======================="

# 获取token
echo "正在获取token..."
TOKEN=$(ssh root@login.uamgo.com 'curl -s -X POST -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin000\"}" "http://localhost:8000/api/auth/login"' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    exit 1
fi

echo "✅ 登录成功"

# 1. 检查当前状态
echo ""
echo "1. 检查当前调度器状态..."
CURRENT_STATUS=$(ssh root@login.uamgo.com "curl -s -H 'Authorization: Bearer $TOKEN' 'http://localhost:8000/api/scheduler/status'")
echo "当前状态: $CURRENT_STATUS"

# 2. 启动定时任务
echo ""
echo "2. 启动定时任务..."
START_RESULT=$(ssh root@login.uamgo.com "curl -s -X POST -H 'Content-Type: application/json' -H 'Authorization: Bearer $TOKEN' -d '{\"enabled\":true,\"cron_expression\":\"20 14 * * 1-5\"}' 'http://localhost:8000/api/scheduler/start'")
echo "启动结果: $START_RESULT"

# 等待1秒
sleep 1

# 3. 再次检查状态
echo ""
echo "3. 启动后的状态..."
AFTER_START=$(ssh root@login.uamgo.com "curl -s -H 'Authorization: Bearer $TOKEN' 'http://localhost:8000/api/scheduler/status'")
echo "启动后状态: $AFTER_START"

# 4. 检查关键字段
echo ""
echo "4. 状态分析..."
if echo "$AFTER_START" | grep -q '"running":true'; then
    echo "✅ running字段为true"
elif echo "$AFTER_START" | grep -q '"running":false'; then
    echo "❌ running字段为false"
else
    echo "⚠️ 未找到running字段"
fi

if echo "$AFTER_START" | grep -q '"enabled":true'; then
    echo "✅ enabled字段为true"
else
    echo "❌ enabled字段不为true"
fi

if echo "$AFTER_START" | grep -q '"job_exists":true'; then
    echo "✅ job_exists字段为true"
else
    echo "❌ job_exists字段不为true"
fi

echo ""
echo "=== 测试完成 ==="
echo "请在浏览器中刷新页面查看按钮状态是否正确更新"
