#!/bin/bash

echo "🔍 股票系统完整诊断脚本"
echo "================================"

# 1. 检查后端服务状态
echo "1. 📊 检查后端服务状态..."
BACKEND_PID=$(ps aux | grep "uvicorn backend.app.main:app" | grep -v grep | awk '{print $2}')
if [ -n "$BACKEND_PID" ]; then
    echo "✅ 后端服务运行中 (PID: $BACKEND_PID)"
else
    echo "❌ 后端服务未运行"
    exit 1
fi

# 2. 检查nginx状态
echo "2. 🌐 检查Nginx状态..."
if docker ps | grep -q nginx; then
    echo "✅ Nginx容器运行中"
else
    echo "❌ Nginx容器未运行"
    exit 1
fi

# 3. 测试本地后端连接
echo "3. 🔗 测试本地后端连接..."
LOCAL_HEALTH=$(curl -s --max-time 5 http://127.0.0.1:8000/api/health)
if [ -n "$LOCAL_HEALTH" ]; then
    echo "✅ 本地后端响应: $LOCAL_HEALTH"
else
    echo "❌ 本地后端无响应"
fi

# 4. 测试nginx代理连接
echo "4. 🔄 测试nginx代理连接..."
PROXY_HEALTH=$(curl -s --max-time 5 http://stock.uamgo.com/api/health)
if [ -n "$PROXY_HEALTH" ]; then
    echo "✅ nginx代理响应: $PROXY_HEALTH"
else
    echo "❌ nginx代理无响应"
fi

# 5. 测试登录API
echo "5. 🔐 测试登录API..."
LOGIN_RESPONSE=$(curl -s --max-time 10 -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}')

echo "登录响应长度: ${#LOGIN_RESPONSE} 字符"
echo "登录响应前200字符:"
echo "$LOGIN_RESPONSE" | head -c 200
echo ""

# 检查登录响应格式
if echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    echo "✅ 登录API返回有效JSON"
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    echo "Token获取成功，长度: ${#TOKEN}"
else
    echo "❌ 登录API返回无效JSON或HTML"
    # 检查是否是HTML
    if echo "$LOGIN_RESPONSE" | grep -q "^<html\|<!DOCTYPE"; then
        echo "🔍 检测到HTML响应，可能是nginx错误页面"
    fi
    exit 1
fi

# 6. 测试股票更新API（短超时）
echo "6. 📈 测试股票更新API（5秒超时）..."
UPDATE_RESPONSE=$(curl -s --max-time 5 -X POST http://stock.uamgo.com/api/stock/update \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"top_n":1}')

echo "更新API响应长度: ${#UPDATE_RESPONSE} 字符"
echo "更新API响应前200字符:"
echo "$UPDATE_RESPONSE" | head -c 200
echo ""

# 检查更新响应格式
if [ ${#UPDATE_RESPONSE} -eq 0 ]; then
    echo "❌ 更新API无响应（可能超时）"
elif echo "$UPDATE_RESPONSE" | grep -q "^<html\|<!DOCTYPE"; then
    echo "❌ 更新API返回HTML页面（nginx超时或错误）"
elif echo "$UPDATE_RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    echo "✅ 更新API返回有效JSON"
    SUCCESS=$(echo "$UPDATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', 'unknown'))" 2>/dev/null)
    MESSAGE=$(echo "$UPDATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'no message'))" 2>/dev/null)
    echo "成功状态: $SUCCESS"
    echo "消息: $MESSAGE"
else
    echo "❌ 更新API返回无效格式"
fi

# 7. 检查nginx配置
echo "7. ⚙️ 检查nginx配置..."
echo "当前nginx配置（stock相关）："
docker exec nginx grep -A 20 "location /api/" /etc/nginx/conf.d/nginx-stock.conf 2>/dev/null || \
docker exec nginx find /etc/nginx -name "*stock*" -exec cat {} \; 2>/dev/null || \
echo "❌ 无法读取nginx配置"

# 8. 检查后端日志
echo "8. 📋 检查后端最近日志..."
echo "最近10行后端日志："
tail -10 /tmp/backend.log 2>/dev/null || echo "❌ 无法读取后端日志"

# 总结
echo ""
echo "🎯 诊断总结："
echo "- 如果登录API正常但更新API返回HTML，说明nginx超时配置有问题"
echo "- 如果更新API超时，需要增加nginx proxy_read_timeout"
echo "- 如果返回JSON但success=false，说明后端逻辑有问题"
echo "- 建议检查nginx配置中的超时设置和后端处理时间"
