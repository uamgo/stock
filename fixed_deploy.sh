#!/bin/bash

# 修正的直接部署脚本 - 使用已有的Python
set -e

SERVER="root@login.uamgo.com"

echo "🚀 开始修正的直接部署..."

# 1. 上传项目文件
echo "📦 创建部署包..."
tar -czf fixed-deploy.tar.gz \
    backend/ \
    tail_trading/ \
    frontend/ \
    deploy/nginx-stock.conf \
    tail_trading.py

echo "📤 上传到服务器..."
scp fixed-deploy.tar.gz $SERVER:/tmp/
scp backend/requirements.txt $SERVER:/tmp/

echo "🔧 在服务器上执行修正部署..."
ssh $SERVER << 'EOF'
set -e

# 解压项目文件
mkdir -p /home/uamgo/stock
cd /home/uamgo/stock
tar -xzf /tmp/fixed-deploy.tar.gz
cp /tmp/requirements.txt ./
rm /tmp/fixed-deploy.tar.gz /tmp/requirements.txt

echo "📦 更新系统包..."
apt-get update

# 安装必要的系统依赖
echo "🔧 安装系统依赖..."
apt-get install -y python3-venv gcc curl

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级pip并配置国内源
echo "⚙️ 配置pip..."
pip install --upgrade pip
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set install.trusted-host mirrors.aliyun.com

# 安装依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

echo "🗂️ 创建启动脚本..."
cat > start_backend.sh << 'START_SCRIPT'
#!/bin/bash
cd /home/uamgo/stock
source venv/bin/activate
export PYTHONPATH=/home/uamgo/stock
export JWT_SECRET_KEY=stock-secret-$(date +%s)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
START_SCRIPT

chmod +x start_backend.sh

echo "📋 创建systemd服务..."
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
Environment=PYTHONPATH=/home/uamgo/stock

[Install]
WantedBy=multi-user.target
SERVICE_FILE

# 停止现有容器和服务
echo "🛑 停止现有服务..."
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true
systemctl stop stock-backend 2>/dev/null || true

# 启动新服务
echo "🚀 启动服务..."
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
echo "🔄 重新加载nginx..."
docker exec nginx nginx -s reload

echo "⏳ 等待服务启动..."
sleep 5

echo "🔍 检查服务状态..."
systemctl status stock-backend --no-pager
ss -tlnp | grep :8000 || echo "端口8000未监听"

# 测试API
echo "🧪 测试API..."
curl -f http://localhost:8000/api/health 2>/dev/null && echo "✅ API健康检查通过" || echo "❌ API健康检查失败"

echo "✅ 部署完成！"
echo "🌐 访问地址: http://stock.uamgo.com"
echo "📊 API地址: http://stock.uamgo.com/api/"

EOF

# 清理
rm fixed-deploy.tar.gz

echo "🎉 修正部署完成！"
