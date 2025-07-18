#!/bin/bash

# 快速部署脚本 - 仅上传必要文件
set -e

SERVER="root@login.uamgo.com"

echo "🚀 开始快速部署..."

# 1. 创建轻量级压缩包
echo "📦 创建部署包..."
tar -czf quick-deploy.tar.gz \
    backend/ \
    tail_trading/ \
    frontend/ \
    Dockerfile.backend \
    deploy/nginx-stock.conf \
    tail_trading.py

echo "📤 上传到服务器..."
scp quick-deploy.tar.gz $SERVER:/tmp/

echo "🔧 在服务器上执行部署..."
ssh $SERVER << 'EOF'
set -e

# 解压项目文件
mkdir -p /home/uamgo/stock
cd /home/uamgo/stock
tar -xzf /tmp/quick-deploy.tar.gz
rm /tmp/quick-deploy.tar.gz

# 配置Docker国内镜像源
echo "🔧 配置Docker镜像加速器..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'DOCKER_CONFIG'
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.ccs.tencentyun.com"
  ]
}
DOCKER_CONFIG

systemctl daemon-reload
systemctl restart docker
sleep 3

# 停止现有容器
echo "🛑 停止现有容器..."
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true

# 构建镜像
echo "🏗️ 构建后端镜像..."
docker build -f Dockerfile.backend -t stock-backend:latest .

# 创建目录
echo "📁 创建必要目录..."
mkdir -p /home/uamgo/stock/{data,logs}
mkdir -p /home/uamgo/nginx/www/stock

# 复制文件
echo "📋 复制前端文件..."
cp -r frontend/* /home/uamgo/nginx/www/stock/

echo "⚙️ 配置nginx..."
cp deploy/nginx-stock.conf /home/uamgo/nginx/conf/

# 启动容器
echo "🚀 启动后端容器..."
docker run -d \
    --name stock-backend \
    --restart unless-stopped \
    -p 8000:8000 \
    -v /home/uamgo/stock/data:/app/data \
    -v /home/uamgo/stock/logs:/app/logs \
    -e PYTHONPATH=/app \
    -e JWT_SECRET_KEY=stock-secret-$(date +%s) \
    stock-backend:latest

# 重新加载nginx
echo "🔄 重新加载nginx..."
docker exec nginx nginx -s reload

echo "⏳ 等待服务启动..."
sleep 5

echo "🔍 检查服务状态..."
docker ps | grep stock-backend
docker logs --tail 10 stock-backend

echo "✅ 部署完成！访问: http://stock.uamgo.com"

EOF

# 清理
rm quick-deploy.tar.gz

echo "🎉 部署完成！"
