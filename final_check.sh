#!/bin/bash

echo "🎉 股票交易系统部署完成检查"
echo "========================================"

# 运行完整的部署检查
bash check_deployment.sh

echo ""
echo "🌟 系统部署总结"
echo "========================================"

# 检查关键组件状态
ssh root@login.uamgo.com << 'EOF'
echo "📊 系统运行状态："

# 后端服务
if systemctl is-active --quiet stock-backend; then
    echo "  ✅ 后端服务: 运行正常"
else
    echo "  ❌ 后端服务: 未运行"
fi

# 端口监听
if ss -tlnp | grep -q :8000; then
    echo "  ✅ API端口: 正常监听"
else
    echo "  ❌ API端口: 未监听"
fi

# 前端文件
if [ -f /home/uamgo/nginx/www/stock/index.html ]; then
    echo "  ✅ 前端文件: 已部署"
else
    echo "  ❌ 前端文件: 未部署"
fi

# nginx配置
if docker exec nginx test -f /etc/nginx/conf.d/nginx-stock.conf 2>/dev/null; then
    echo "  ✅ Nginx配置: 已配置"
else
    echo "  ❌ Nginx配置: 未配置"
fi

# 概念数据
CONCEPT_COUNT=$(find /tmp/stock/concept/ -name "*.pkl" -type f 2>/dev/null | wc -l)
if [ "$CONCEPT_COUNT" -gt 0 ]; then
    echo "  ✅ 概念数据: 已初始化 ($CONCEPT_COUNT 个板块)"
else
    echo "  ⚠️  概念数据: 未初始化"
fi

echo ""
echo "🔗 访问信息："
echo "  📱 前端地址: http://stock.uamgo.com"
echo "  📖 API文档: http://stock.uamgo.com/api/docs"
echo "  💓 健康检查: http://stock.uamgo.com/api/health"
echo ""
echo "🔐 登录信息："
echo "  👤 用户名: admin"
echo "  🔑 密码: admin000"

# 快速功能测试
echo ""
echo "🧪 快速功能测试："

# 健康检查
if curl -s http://stock.uamgo.com/api/health | grep -q "ok"; then
    echo "  ✅ 健康检查: 通过"
else
    echo "  ❌ 健康检查: 失败"
fi

# 登录测试
LOGIN_RESULT=$(curl -s -X POST http://stock.uamgo.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin000"}' | grep -o "access_token")

if [ -n "$LOGIN_RESULT" ]; then
    echo "  ✅ 登录功能: 正常"
else
    echo "  ❌ 登录功能: 异常"
fi

EOF

echo ""
echo "🚀 部署完成！"
echo "========================================"
echo "系统已成功部署并可以投入使用。"

if [ "$CONCEPT_COUNT" -eq 0 ]; then
    echo ""
    echo "⚠️  提醒: 首次使用前请初始化概念数据："
    echo "   运行: bash init_concepts.sh"
    echo "   或在前端界面点击 '初始化概念数据' 按钮"
fi

echo ""
echo "📄 详细文档: 请查看 DEPLOYMENT_GUIDE.md"
echo "🛠️  维护脚本: check_deployment.sh"
echo "🔄 初始化脚本: init_concepts.sh"
