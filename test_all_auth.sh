#!/bin/bash

echo "🔐 完整API鉴权检查..."

# 获取token
echo "1. 获取认证token..."
LOGIN_RESPONSE=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin000"}')

if echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "✅ Token获取成功: ${TOKEN:0:20}..."
else
    echo "❌ 登录失败"
    exit 1
fi

# 测试无需鉴权的接口
echo ""
echo "2. 测试无需鉴权的接口..."
echo "健康检查: $(curl -s http://stock.uamgo.com/api/health | python3 -c "import sys, json; print('✅' if json.load(sys.stdin).get('status') == 'ok' else '❌')" 2>/dev/null || echo '❌')"

# 测试需要鉴权的接口
echo ""
echo "3. 测试需要鉴权的接口..."

test_auth_api() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    local cmd="curl -s -X $method"
    if [ -n "$data" ]; then
        cmd="$cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    cmd="$cmd -H 'Authorization: Bearer $TOKEN' 'http://stock.uamgo.com$endpoint'"
    
    local response=$(eval $cmd)
    local status="❌"
    
    if echo "$response" | grep -q "Invalid authentication credentials\|Unauthorized\|401"; then
        status="❌ 鉴权失败"
    elif echo "$response" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        status="✅ 鉴权正常"
    elif [ ${#response} -eq 0 ]; then
        status="⏳ 无响应/超时"
    else
        status="⚠️  响应异常"
    fi
    
    printf "%-20s: %s\n" "$name" "$status"
}

# 用户相关接口
test_auth_api "用户信息" "GET" "/api/auth/me" ""
test_auth_api "用户列表" "GET" "/api/users" ""

# 股票相关接口 
test_auth_api "数据更新" "POST" "/api/stock/update" '{"top_n":1}'
test_auth_api "选股" "POST" "/api/stock/select" '{"preset":"balanced","limit":3,"verbose":false}'
test_auth_api "概念初始化" "POST" "/api/stock/init-concepts" ""

# 调度器相关接口
test_auth_api "调度器状态" "GET" "/api/scheduler/status" ""
test_auth_api "调度器日志" "GET" "/api/scheduler/logs?lines=10" ""

echo ""
echo "4. 测试SSE流式接口鉴权..."
SSE_RESPONSE=$(timeout 3 curl -s -H "Authorization: Bearer $TOKEN" \
  "http://stock.uamgo.com/api/stock/update-stream?top_n=1" | head -1)

if echo "$SSE_RESPONSE" | grep -q "data:"; then
    echo "SSE流式接口      : ✅ 鉴权正常"
elif echo "$SSE_RESPONSE" | grep -q "Invalid authentication\|401"; then
    echo "SSE流式接口      : ❌ 鉴权失败"
else
    echo "SSE流式接口      : ⚠️  响应异常"
fi

echo ""
echo "5. 测试无效token..."
INVALID_RESPONSE=$(curl -s -H "Authorization: Bearer invalid_token_123" \
  "http://stock.uamgo.com/api/auth/me")

if echo "$INVALID_RESPONSE" | grep -q "Invalid authentication\|Unauthorized"; then
    echo "无效token处理    : ✅ 正确拒绝"
else
    echo "无效token处理    : ❌ 安全问题"
fi

echo ""
echo "🎯 API鉴权检查完成！"
