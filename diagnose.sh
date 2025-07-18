#!/bin/bash

echo "🔍 股票系统问题诊断报告"
echo "========================================"

echo ""
echo "📊 1. 系统运行状态"
ssh root@login.uamgo.com << 'EOF'
echo "后端服务状态:"
systemctl is-active stock-backend

echo "进程列表:"
ps aux | grep python3 | grep -v grep

echo "端口监听:"
ss -tlnp | grep :8000

echo "内存使用:"
free -h

echo "磁盘空间:"
df -h /tmp

echo ""
echo "📁 2. 数据目录状态"
echo "概念数据文件数量:"
find /tmp/stock/concept/ -name "*.pkl" -type f 2>/dev/null | wc -l

echo "基础数据文件:"
ls -la /tmp/stock/base/ 2>/dev/null || echo "基础数据目录不存在"

echo "数据目录大小:"
du -sh /tmp/stock/ 2>/dev/null || echo "数据目录不存在"

echo ""
echo "🌐 3. 网络连接测试"
echo "内部健康检查:"
curl -s --connect-timeout 5 http://localhost:8000/api/health || echo "内部连接失败"

echo "外部健康检查:"
curl -s --connect-timeout 5 http://stock.uamgo.com/api/health || echo "外部连接失败"

echo "nginx代理测试:"
docker exec nginx curl -s --connect-timeout 5 http://172.19.0.1:8000/api/health || echo "nginx代理失败"

EOF

echo ""
echo "🐛 4. 常见问题和解决方案"
echo "========================================"
echo "问题1: JSON解析错误"
echo "原因: API返回HTML错误页面而不是JSON"
echo "解决: 检查后端服务状态，确保API正常运行"
echo ""
echo "问题2: 数据更新超时"
echo "原因: 网络延迟或数据源响应慢"
echo "解决: 减少更新数量(top_n)，或增加超时时间"
echo ""
echo "问题3: 概念数据缺失"
echo "原因: 首次使用需要初始化概念板块数据"
echo "解决: 运行 bash init_concepts.sh"
echo ""
echo "📋 5. 建议操作"
echo "========================================"
echo "1. 如果数据更新失败，尝试更小的数量: top_n = 3"
echo "2. 定期清理临时数据: rm -rf /tmp/stock/daily/*"
echo "3. 监控进程状态: ps aux | grep tail_trading"
echo "4. 查看详细日志: journalctl -u stock-backend -f"
