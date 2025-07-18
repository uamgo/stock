#!/bin/bash

echo "=== 测试股票系统的5项新功能 ==="

# 1. 测试默认定时任务时间（每工作日下午2:20）
echo "1. 测试定时任务配置..."
ssh root@login.uamgo.com 'curl -s -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1Mjg1MTk1M30.xKNbRUTo_SmSBk9GvVXJzzfmg0_SeusEMp-bjV6xCVs" "http://localhost:8000/api/scheduler/status"' | grep -o "工作日\|14:20\|2:20" || echo "定时任务配置待验证"

# 2. 测试日期目录创建
echo "2. 测试日期目录..."
TODAY=$(date +%Y-%m-%d)
ssh root@login.uamgo.com "ls -la /tmp/$TODAY/" && echo "✅ 日期目录创建成功" || echo "❌ 日期目录创建失败"

# 3. 测试已存在选股结果加载
echo "3. 测试已存在选股结果加载..."
RESULT=$(ssh root@login.uamgo.com 'curl -s -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1Mjg1MTk1M30.xKNbRUTo_SmSBk9GvVXJzzfmg0_SeusEMp-bjV6xCVs" "http://localhost:8000/api/stock/existing-results"')
echo "$RESULT" | grep -q "找到 3 只股票" && echo "✅ 已存在选股结果加载成功" || echo "❌ 已存在选股结果加载失败"

# 4. 测试前端页面加载
echo "4. 测试前端页面访问..."
curl -s -o /dev/null -w "%{http_code}" http://login.uamgo.com/stock/ | grep -q "200" && echo "✅ 前端页面访问正常" || echo "❌ 前端页面访问失败"

# 5. 检查导出功能代码
echo "5. 检查导出功能..."
ssh root@login.uamgo.com 'grep -q "exportResults" /var/lib/docker/volumes/uamgo/_data/nginx/stock/app.js' && echo "✅ 导出功能代码已部署" || echo "❌ 导出功能代码未找到"

echo "=== 测试完成 ==="
echo "请在浏览器中打开 http://login.uamgo.com/stock/ 进行最终验证"
echo "默认账号: admin"
echo "默认密码: admin000"
