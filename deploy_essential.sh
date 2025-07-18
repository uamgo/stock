#!/bin/bash

# 精简部署脚本 - 只上传必要文件
set -e

SERVER="root@login.uamgo.com"
REMOTE_PROJECT_DIR="/home/uamgo/stock"

echo "🚀 开始精简部署..."

# 1. 创建必要文件的压缩包
echo "📦 创建必要文件压缩包..."
tar -czf essential-files.tar.gz \
    backend/ \
    tail_trading/ \
    frontend/ \
    data/ \
    Dockerfile.backend \
    deploy/nginx-stock.conf \
    tail_trading.py \
    requirements.txt

echo "📤 上传文件到服务器..."
scp essential-files.tar.gz $SERVER:/tmp/

echo "🔧 在服务器上执行部署..."
ssh $SERVER << 'EOF'
set -e

# 配置Docker国内镜像源
echo "🔧 配置Docker镜像加速器..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'DOCKER_CONFIG'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://registry.docker-cn.com"
  ],
  "insecure-registries": [],
  "experimental": false,
  "features": {
    "buildkit": true
  }
}
DOCKER_CONFIG

systemctl daemon-reload
systemctl restart docker
sleep 5

# 创建项目目录并解压
mkdir -p /home/uamgo/stock
cd /home/uamgo/stock
tar -xzf /tmp/essential-files.tar.gz
rm /tmp/essential-files.tar.gz

# 停止并删除现有容器
echo "🛑 停止现有容器..."
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true

# 构建新镜像
echo "🏗️ 构建后端镜像..."
docker build -f Dockerfile.backend -t stock-backend:latest .

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p /home/uamgo/stock/data
mkdir -p /home/uamgo/stock/logs
mkdir -p /home/uamgo/nginx/www/stock

# 复制前端文件到nginx目录
echo "📋 复制前端文件..."
cp -r frontend/* /home/uamgo/nginx/www/stock/

# 复制nginx配置文件
echo "⚙️ 配置nginx..."
cp deploy/nginx-stock.conf /home/uamgo/nginx/conf/

# 启动后端容器
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

# 重新加载nginx配置
echo "🔄 重新加载nginx配置..."
docker exec nginx nginx -s reload

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker logs --tail 20 stock-backend

echo "✅ 部署完成！"
echo "🌐 访问地址: http://stock.uamgo.com"

EOF

# 清理本地临时文件
rm essential-files.tar.gz

echo "🎉 部署完成！请访问 http://stock.uamgo.com"
