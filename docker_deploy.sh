#!/bin/bash

# Docker容器部署脚本 - 使用本地可用镜像
set -e

SERVER="root@login.uamgo.com"

echo "🚀 开始Docker容器部署..."

# 1. 检查服务器上可用的镜像
echo "🔍 检查服务器镜像..."
ssh $SERVER "docker images"

echo "📦 上传Dockerfile和项目文件..."
# 上传Ubuntu版本的Dockerfile
scp Dockerfile.backend.ubuntu $SERVER:/tmp/Dockerfile.backend

# 创建项目压缩包
tar -czf docker-deploy.tar.gz \
    backend/ \
    tail_trading/ \
    frontend/ \
    deploy/nginx-stock.conf \
    tail_trading.py

scp docker-deploy.tar.gz $SERVER:/tmp/

echo "🔧 在服务器上执行Docker部署..."
ssh $SERVER << 'EOF'
set -e

# 清理旧的部署
systemctl stop stock-backend 2>/dev/null || true
systemctl disable stock-backend 2>/dev/null || true
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true

# 解压项目文件
mkdir -p /home/uamgo/stock
cd /home/uamgo/stock
tar -xzf /tmp/docker-deploy.tar.gz
cp /tmp/Dockerfile.backend ./
rm /tmp/docker-deploy.tar.gz /tmp/Dockerfile.backend

# 尝试拉取Ubuntu镜像（如果失败则使用现有方法）
echo "🔽 尝试拉取Ubuntu基础镜像..."
if docker pull ubuntu:20.04; then
    echo "✅ Ubuntu镜像拉取成功"
    
    # 构建应用镜像
    echo "🏗️ 构建股票应用镜像..."
    docker build -f Dockerfile.backend -t stock-backend:latest .
    
    # 创建目录
    mkdir -p /home/uamgo/stock/{data,logs}
    mkdir -p /home/uamgo/nginx/www/stock
    
    # 复制前端文件
    echo "📋 部署前端文件..."
    cp -r frontend/* /home/uamgo/nginx/www/stock/
    
    # 配置nginx
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
    docker exec nginx nginx -s reload
    
    echo "⏳ 等待服务启动..."
    sleep 10
    
    echo "🔍 检查服务状态..."
    docker ps | grep stock-backend
    docker logs --tail 20 stock-backend
    
    # 测试API
    curl -f http://localhost:8000/api/health 2>/dev/null && echo "✅ API健康检查通过" || echo "❌ API健康检查失败"
    
    echo "✅ Docker容器部署完成！"
    echo "🌐 访问地址: http://stock.uamgo.com"
    
else
    echo "❌ 无法拉取Ubuntu镜像，网络连接有问题"
    echo "💡 建议检查网络连接或使用离线部署方案"
    exit 1
fi

EOF

# 清理本地文件
rm docker-deploy.tar.gz

echo "🎉 Docker部署完成！"
