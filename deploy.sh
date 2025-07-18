#!/bin/bash

# 股票项目部署脚本
# 目标服务器: login.uamgo.com
# 域名: stock.uamgo.com

set -e

# 配置变量
SERVER="root@login.uamgo.com"
REMOTE_PROJECT_DIR="/home/uamgo/stock"
NGINX_WWW_DIR="/home/uamgo/nginx/www/stock"
NGINX_CONF_DIR="/home/uamgo/nginx/conf"
CONTAINER_NAME="stock-backend"
IMAGE_NAME="stock-backend:latest"

echo "🚀 开始部署股票项目..."

# 1. 创建项目压缩包并传输到服务器
echo "📦 创建项目压缩包..."
tar --exclude='node_modules' \
    --exclude='.git' \
    --exclude='data/cache/*' \
    --exclude='logs/*' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='stock-project.tar.gz' \
    -czf stock-project.tar.gz .

echo "📤 上传项目文件到服务器..."
scp stock-project.tar.gz $SERVER:/tmp/

echo "📦 在服务器上解压项目文件..."
ssh $SERVER "mkdir -p $REMOTE_PROJECT_DIR && cd $REMOTE_PROJECT_DIR && tar -xzf /tmp/stock-project.tar.gz && rm /tmp/stock-project.tar.gz"

echo "🧹 清理本地临时文件..."
rm stock-project.tar.gz

# 2. 在服务器上执行部署命令
echo "🔧 在服务器上执行部署..."
ssh $SERVER << 'EOF'
set -e

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

# 切换到项目目录
cd /home/uamgo/stock

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
    -e JWT_SECRET_KEY=your-production-secret-key-$(date +%s) \
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
echo "📊 API地址: http://stock.uamgo.com/api/"

EOF

echo "🎉 部署脚本执行完成！"
echo "请访问 http://stock.uamgo.com 查看应用"
