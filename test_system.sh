#!/bin/bash

# 系统功能测试脚本

API_BASE="http://localhost:8000/api"
TOKEN=""

echo "=========================================="
echo "Tail Trading 系统功能测试"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_api() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"
    
    echo -n "测试 $name ... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$API_BASE$endpoint")
    else
        response=$(curl -s -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "$data" "$API_BASE$endpoint")
    fi
    
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ 通过${NC} (HTTP $status_code)"
        return 0
    else
        echo -e "${RED}✗ 失败${NC} (HTTP $status_code)"
        echo "响应: $body"
        return 1
    fi
}

# 1. 测试健康检查
test_api "健康检查" "GET" "/health" "" "200"

# 2. 测试登录
echo -n "测试用户登录 ... "
login_response=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"admin000"}' "$API_BASE/auth/login")
if echo "$login_response" | grep -q "access_token"; then
    TOKEN=$(echo "$login_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo -e "${GREEN}✓ 通过${NC}"
else
    echo -e "${RED}✗ 失败${NC}"
    echo "响应: $login_response"
    exit 1
fi

# 3. 测试获取当前用户信息
test_api "获取用户信息" "GET" "/auth/me" "" "200"

# 4. 测试获取用户列表
test_api "获取用户列表" "GET" "/users" "" "200"

# 5. 测试定时任务状态
test_api "获取定时任务状态" "GET" "/scheduler/status" "" "200"

# 6. 测试数据更新（模拟，可能会超时）
echo -n "测试数据更新接口 ... "
echo -e "${YELLOW}跳过（耗时较长）${NC}"

# 7. 测试选股接口（模拟，可能会超时）
echo -n "测试选股接口 ... "
echo -e "${YELLOW}跳过（耗时较长）${NC}"

echo ""
echo "=========================================="
echo "基础API测试完成"
echo "=========================================="
echo ""
echo "手动测试项目："
echo "1. 访问前端界面: http://localhost:3000 或 http://localhost"
echo "2. 登录系统（admin/admin000）"
echo "3. 测试数据更新功能"
echo "4. 测试选股功能"
echo "5. 测试定时任务功能"
echo "6. 测试日志查看功能"
echo "7. 测试数据导出功能"
