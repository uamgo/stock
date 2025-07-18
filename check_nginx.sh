#!/bin/bash

echo "🔍 检查Nginx状态和配置..."

# 检查nginx容器状态
echo "=== Nginx容器状态 ==="
ssh root@login.uamgo.com "docker ps -a | grep nginx"

# 检查nginx配置文件是否存在
echo "=== Nginx配置文件 ==="
ssh root@login.uamgo.com "ls -la /home/uamgo/nginx/conf/"

# 检查nginx配置文件内容
echo "=== Nginx配置文件内容 ==="
ssh root@login.uamgo.com "cat /home/uamgo/nginx/conf/nginx-stock.conf"

# 在nginx容器内检查配置
echo "=== 容器内的Nginx配置 ==="
ssh root@login.uamgo.com "docker exec nginx-stock nginx -t"

# 检查端口绑定
echo "=== 端口绑定状态 ==="
ssh root@login.uamgo.com "docker port nginx-stock"

# 测试从容器内访问后端
echo "=== 从容器内测试后端连接 ==="
ssh root@login.uamgo.com "docker exec nginx-stock curl -s http://172.17.0.1:8000/api/health || echo '连接失败'"

# 测试域名访问
echo "=== 测试域名访问 ==="
ssh root@login.uamgo.com "curl -s -H 'Host: stock.uamgo.com' http://localhost:80/api/health || echo '域名访问失败'"

# 重新加载nginx配置
echo "=== 重新加载nginx配置 ==="
ssh root@login.uamgo.com "docker exec nginx-stock nginx -s reload"

echo "检查完成！"
