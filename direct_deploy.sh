#!/bin/bash

# 无Docker依赖的直接部署脚本
set -e

SERVER="root@login.uamgo.com"

echo "🚀 开始无Docker依赖部署..."

# 1. 上传项目文件
echo "📦 创建部署包..."
tar -czf simple-deploy.tar.gz \
    backend/ \
    tail_trading/ \
    frontend/ \
    deploy/nginx-stock.conf \
    tail_trading.py \
    requirements.txt

echo "📤 上传到服务器..."
scp simple-deploy.tar.gz $SERVER:/tmp/

echo "🔧 在服务器上执行直接部署..."
ssh $SERVER << 'EOF'
set -e

# 解压项目文件
mkdir -p /home/uamgo/stock
cd /home/uamgo/stock
tar -xzf /tmp/simple-deploy.tar.gz
rm /tmp/simple-deploy.tar.gz

echo "📦 安装Python和依赖..."
# 更新系统
apt-get update

# 安装Python 3.11
apt-get install -y python3.11 python3.11-pip python3.11-dev python3.11-venv gcc curl

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 配置pip使用阿里云源
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set install.trusted-host mirrors.aliyun.com

# 安装依赖
cd /home/uamgo/stock
pip install -r requirements.txt

# 创建启动脚本
cat > start_backend.sh << 'START_SCRIPT'
#!/bin/bash
cd /home/uamgo/stock
source venv/bin/activate
export PYTHONPATH=/home/uamgo/stock
export JWT_SECRET_KEY=stock-secret-$(date +%s)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
START_SCRIPT

chmod +x start_backend.sh

# 创建systemd服务
cat > /etc/systemd/system/stock-backend.service << 'SERVICE_FILE'
[Unit]
Description=Stock Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/uamgo/stock
ExecStart=/home/uamgo/stock/start_backend.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE_FILE

# 停止现有容器（如果有）
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true

# 启动新服务
systemctl daemon-reload
systemctl enable stock-backend
systemctl start stock-backend

echo "📁 创建必要目录..."
mkdir -p /home/uamgo/stock/{data,logs}
mkdir -p /home/uamgo/nginx/www/stock

echo "📋 复制前端文件..."
cp -r frontend/* /home/uamgo/nginx/www/stock/

echo "⚙️ 配置nginx..."
cp deploy/nginx-stock.conf /home/uamgo/nginx/conf/

# 重新加载nginx
docker exec nginx nginx -s reload

echo "⏳ 等待服务启动..."
sleep 5

echo "🔍 检查服务状态..."
systemctl status stock-backend --no-pager
ss -tlnp | grep :8000

echo "✅ 部署完成！访问: http://stock.uamgo.com"

EOF

# 清理
rm simple-deploy.tar.gz

echo "🎉 直接部署完成！"
