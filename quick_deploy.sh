#!/bin/bash

# 快速部署脚本 - 仅更新代码和重启服务
# 用于日常更新，跳过初始化步骤

set -e

SERVER="root@login.uamgo.com"
REMOTE_PROJECT_DIR="/home/uamgo/stock"

echo "🔄 快速更新部署..."

# 1. 同步代码
echo "📦 同步代码..."

# 创建临时压缩包
echo "创建后端代码压缩包..."
tar -czf backend.tar.gz backend/
tar -czf tail_trading.tar.gz tail_trading/
tar -czf frontend.tar.gz frontend/

# 上传到服务器
scp backend.tar.gz tail_trading.tar.gz frontend.tar.gz tail_trading.py $SERVER:/tmp/

# 在服务器上解压
ssh $SERVER << 'EXTRACT_EOF'
cd /home/uamgo/stock
tar -xzf /tmp/backend.tar.gz
tar -xzf /tmp/tail_trading.tar.gz
cp /tmp/tail_trading.py ./
cd /home/uamgo/nginx/www
tar -xzf /tmp/frontend.tar.gz
mv frontend stock
rm /tmp/*.tar.gz /tmp/tail_trading.py
EXTRACT_EOF

# 清理本地临时文件
rm backend.tar.gz tail_trading.tar.gz frontend.tar.gz

# 3. 重启后端服务
echo "🔄 重启后端服务..."
ssh $SERVER << 'EOF'
cd /home/uamgo/stock

# 确保Docker使用国内镜像源
echo "🔧 检查Docker镜像源配置..."
if [ ! -f /etc/docker/daemon.json ]; then
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << 'DOCKER_CONFIG'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn", 
    "https://hub-mirror.c.163.com",
    "https://registry.docker-cn.com"
  ]
}
DOCKER_CONFIG
    systemctl daemon-reload
    systemctl restart docker
    sleep 5
fi

# 重新构建并重启容器
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true
docker build -f Dockerfile.backend -t stock-backend:latest .

docker run -d \
    --name stock-backend \
    --restart unless-stopped \
    -p 8000:8000 \
    -v /home/uamgo/stock/data:/app/data \
    -v /home/uamgo/stock/logs:/app/logs \
    -e PYTHONPATH=/app \
    -e JWT_SECRET_KEY=your-production-secret-key-$(date +%s) \
    stock-backend:latest

# 检查状态
sleep 5
docker logs --tail 10 stock-backend
EOF

echo "✅ 快速更新完成！"
