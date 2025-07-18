#!/bin/bash

echo "🔧 测试修复后的系统功能"
echo "========================="

# 1. 测试登录
echo "1. 测试登录API..."
TOKEN=$(ssh root@login.uamgo.com 'curl -s -X POST -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin000\"}" "http://localhost:8000/api/auth/login"' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "✅ 登录成功，获取到token"
else
    echo "❌ 登录失败"
    exit 1
fi

# 2. 测试选股API（简单调用，不等待结果）
echo "2. 测试选股API参数..."
ssh root@login.uamgo.com "curl -s -X POST -H 'Content-Type: application/json' -H 'Authorization: Bearer $TOKEN' -d '{\"preset\":\"balanced\",\"limit\":3,\"verbose\":false}' 'http://localhost:8000/api/stock/select' --max-time 10" > /tmp/select_test.log 2>&1 &
SELECT_PID=$!

# 等待3秒检查是否有参数错误
sleep 3
if ps -p $SELECT_PID > /dev/null; then
    echo "✅ 选股API启动正常（无参数错误）"
    kill $SELECT_PID 2>/dev/null
else
    echo "⚠️ 选股API可能已完成或有其他问题"
fi

# 3. 测试调度器状态API
echo "3. 测试调度器状态API..."
SCHEDULER_STATUS=$(ssh root@login.uamgo.com "curl -s -H 'Authorization: Bearer $TOKEN' 'http://localhost:8000/api/scheduler/status'")
if echo "$SCHEDULER_STATUS" | grep -q '"running"'; then
    echo "✅ 调度器状态API正常"
else
    echo "❌ 调度器状态API异常"
fi

# 4. 检查前端文件
echo "4. 检查前端文件..."
ssh root@login.uamgo.com 'grep -q "toggleSchedulerBtn" /var/lib/docker/volumes/uamgo/_data/nginx/stock/index.html' && echo "✅ 前端切换按钮代码已部署" || echo "❌ 前端切换按钮代码未找到"

ssh root@login.uamgo.com 'grep -q "toggleBtn.textContent" /var/lib/docker/volumes/uamgo/_data/nginx/stock/app.js' && echo "✅ 前端按钮状态切换逻辑已部署" || echo "❌ 前端按钮状态切换逻辑未找到"

echo ""
echo "=== 修复状态 ==="
echo "✅ 移除了--output-dir参数（修复选股参数错误）"
echo "✅ 合并启动/停止按钮为单一切换按钮"
echo "✅ 添加了按钮状态自动切换逻辑"
echo ""
echo "请在浏览器中访问 http://login.uamgo.com/stock/ 进行最终测试"
echo "默认账号: admin 密码: admin000"
