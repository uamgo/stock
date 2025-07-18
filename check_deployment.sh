#!/bin/bash

# 部署状态检查脚本
SERVER="root@login.uamgo.com"

echo "🔍 检查股票应用部署状态..."

ssh $SERVER << 'EOF'
echo "=== 后端服务状态 ==="
systemctl status stock-backend --no-pager -l

echo -e "\n=== 端口监听状态 ==="
ss -tlnp | grep :8000

echo -e "\n=== API健康检查 ==="
curl -s http://localhost:8000/api/health || echo "API健康检查失败"

echo -e "\n=== 前端文件 ==="
ls -la /home/uamgo/nginx/www/stock/

echo -e "\n=== Nginx配置 ==="
ls -la /home/uamgo/nginx/conf/nginx-stock.conf

echo -e "\n=== 服务日志（最近10行）==="
journalctl -u stock-backend --no-pager -n 10

echo -e "\n=== Nginx日志检查 ==="
echo "Nginx访问日志（最近5行）："
timeout 5 docker exec nginx tail -5 /var/log/nginx/access.log 2>/dev/null || echo "无法访问nginx访问日志"

echo -e "\nNginx错误日志（最近5行）："
timeout 5 docker exec nginx tail -5 /var/log/nginx/error.log 2>/dev/null || echo "无法访问nginx错误日志"

echo -e "\n=== Docker网络检查 ==="
echo "Docker网桥信息："
ip addr show docker0 | grep -E "inet|state" || echo "docker0网桥不存在"

echo -e "\n=== 主机网络端口 ==="
echo "8000端口详细信息："
ss -tlnp | grep :8000

echo -e "\n=== 网络连接测试 ==="
echo "测试nginx到后端的连接："
docker exec nginx curl -s --connect-timeout 5 http://172.19.0.1:8000/api/health || echo "nginx无法连接到后端"

echo -e "\n=== 部署完成情况总结 ==="
echo "✅ 后端服务: $(systemctl is-active stock-backend)"
echo "✅ 端口8000: $(ss -tlnp | grep :8000 > /dev/null && echo '正在监听' || echo '未监听')"
echo "✅ 前端文件: $([ -f /home/uamgo/nginx/www/stock/index.html ] && echo '已部署' || echo '未部署')"
echo "✅ Nginx配置: $([ -f /home/uamgo/nginx/conf/nginx-stock.conf ] && echo '已配置' || echo '未配置')"

echo -e "\n=== 功能测试 ==="
echo "测试登录API..."
LOGIN_TEST=$(curl -s -X POST http://stock.uamgo.com/api/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin000"}')
if echo "$LOGIN_TEST" | grep -q "access_token"; then
    echo "✅ 登录功能正常"
else
    echo "❌ 登录功能异常"
fi

echo -e "\n🌐 访问地址:"
echo "- 前端应用: http://stock.uamgo.com"
echo "- API文档: http://stock.uamgo.com/api/docs"
echo "- API健康检查: http://stock.uamgo.com/api/health"

echo -e "\n📝 初始化说明:"
echo "⚠️  首次使用需要初始化概念数据，有两种方式："
echo "   1. 前端操作：登录后点击 '初始化概念数据' 按钮"
echo "   2. 命令行：bash init_concepts.sh"

echo -e "\n=== 概念数据状态 ==="
CONCEPT_COUNT=$(find /tmp/stock/concept/ -name "*.pkl" -type f 2>/dev/null | wc -l)
echo "已下载概念板块数据: $CONCEPT_COUNT 个"
if [ "$CONCEPT_COUNT" -gt 0 ]; then
    echo "✅ 概念数据已初始化，可以正常使用"
else
    echo "⚠️  概念数据未初始化，需要先运行初始化"
fi

EOF
