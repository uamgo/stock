#!/bin/bash

# 服务器状态检查脚本

SERVER="root@login.uamgo.com"

echo "🔍 检查服务器状态..."

ssh $SERVER << 'EOF'
echo "=== 系统信息 ==="
uname -a
echo

echo "=== Docker 容器状态 ==="
docker ps | grep -E "(nginx|stock-backend)"
echo

echo "=== 股票后端容器日志 ==="
docker logs --tail 20 stock-backend 2>/dev/null || echo "股票后端容器未运行"
echo

echo "=== 磁盘使用情况 ==="
df -h | grep -E "(/$|/home)"
echo

echo "=== 内存使用情况 ==="
free -h
echo

echo "=== 网络端口检查 ==="
netstat -tlnp | grep -E "(:80|:8000)"
echo

echo "=== 项目目录 ==="
ls -la /home/uamgo/stock/ 2>/dev/null || echo "/home/uamgo/stock 目录不存在"
echo

echo "=== Nginx WWW 目录 ==="
ls -la /home/uamgo/nginx/www/stock/ 2>/dev/null || echo "/home/uamgo/nginx/www/stock 目录不存在"

EOF
