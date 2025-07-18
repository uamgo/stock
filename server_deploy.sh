#!/bin/bash

# 服务器端部署脚本
# 在服务器上运行此脚本完成部署

set -e

cd /home/uamgo/stock

echo "🛑 停止现有容器..."
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true

echo "🏗️ 构建后端镜像..."
docker build -f Dockerfile.backend -t stock-backend:latest .

echo "📁 创建必要的目录..."
mkdir -p /home/uamgo/stock/data
mkdir -p /home/uamgo/stock/logs
mkdir -p /home/uamgo/nginx/www/stock

echo "📋 复制前端文件..."
cp -r frontend/* /home/uamgo/nginx/www/stock/

echo "⚙️ 配置nginx..."
cp deploy/nginx-stock.conf /home/uamgo/nginx/conf/

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

echo "🔄 重新加载nginx配置..."
docker exec nginx nginx -s reload

echo "⏳ 等待服务启动..."
sleep 10

echo "🔍 检查服务状态..."
docker logs --tail 20 stock-backend

echo "✅ 部署完成！"
echo "🌐 访问地址: http://stock.uamgo.com"
echo "📊 API地址: http://stock.uamgo.com/api/"
