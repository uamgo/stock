#!/bin/bash

# 测试不同Docker镜像的可用性
set -e

SERVER="root@login.uamgo.com"

echo "🧪 测试不同Docker镜像..."

# 测试1：Alpine镜像
echo "📋 测试1: 使用Alpine镜像..."
scp Dockerfile.backend.alpine $SERVER:/home/uamgo/stock/Dockerfile.backend.test

ssh $SERVER << 'EOF'
cd /home/uamgo/stock
echo "拉取Alpine镜像..."
docker pull alpine:latest || { echo "Alpine镜像拉取失败"; exit 1; }

echo "构建Alpine版本..."
docker build -f Dockerfile.backend.test -t stock-backend-alpine:test . || { echo "Alpine构建失败"; exit 1; }

echo "✅ Alpine版本构建成功"
docker images | grep stock-backend-alpine
EOF

if [ $? -eq 0 ]; then
    echo "✅ Alpine镜像可用，准备正式部署"
    
    # 使用Alpine版本进行部署
    echo "🚀 使用Alpine版本部署..."
    ssh $SERVER << 'DEPLOY_EOF'
cd /home/uamgo/stock

# 停止现有容器
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true

# 使用Alpine版本
cp Dockerfile.backend.test Dockerfile.backend
docker build -f Dockerfile.backend -t stock-backend:latest .

# 创建目录
mkdir -p /home/uamgo/stock/{data,logs}
mkdir -p /home/uamgo/nginx/www/stock

# 复制前端文件
cp -r frontend/* /home/uamgo/nginx/www/stock/

# 配置nginx
cp deploy/nginx-stock.conf /home/uamgo/nginx/conf/

# 启动容器
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
docker exec nginx nginx -s reload

echo "⏳ 等待服务启动..."
sleep 5

echo "🔍 检查服务状态..."
docker ps | grep stock-backend
docker logs --tail 10 stock-backend

echo "✅ 部署完成！访问: http://stock.uamgo.com"
DEPLOY_EOF

else
    echo "❌ Alpine镜像不可用，尝试其他方案"
fi
