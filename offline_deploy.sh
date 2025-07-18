#!/bin/bash

# 完全离线部署方案 - 不依赖外部镜像拉取
set -e

SERVER="root@login.uamgo.com"

echo "🚀 开始离线部署方案..."

# 创建项目压缩包
echo "📦 创建项目包..."
tar -czf offline-deploy.tar.gz \
    backend/ \
    tail_trading/ \
    frontend/ \
    deploy/nginx-stock.conf \
    tail_trading.py

scp offline-deploy.tar.gz $SERVER:/tmp/

echo "🔧 在服务器上执行离线部署..."
ssh $SERVER << 'EOF'
set -e

# 清理之前的部署
systemctl stop stock-backend 2>/dev/null || true
systemctl disable stock-backend 2>/dev/null || true
docker stop stock-backend 2>/dev/null || true
docker rm stock-backend 2>/dev/null || true

# 解压项目
mkdir -p /home/uamgo/stock
cd /home/uamgo/stock
tar -xzf /tmp/offline-deploy.tar.gz
rm /tmp/offline-deploy.tar.gz

echo "📦 安装系统Python环境..."
# 使用系统Python直接运行
apt-get update -qq
apt-get install -y python3-venv python3-pip gcc > /dev/null 2>&1

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 配置pip使用国内源
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set install.trusted-host mirrors.aliyun.com

# 创建requirements.txt（如果不存在）
cat > requirements.txt << 'REQUIREMENTS'
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.5.0
croniter==1.4.1
apscheduler==3.10.4
python-dotenv==1.0.0
REQUIREMENTS

echo "📦 安装Python依赖..."
pip install -r requirements.txt

echo "🗂️ 创建启动脚本..."
cat > start_backend.sh << 'START_SCRIPT'
#!/bin/bash
cd /home/uamgo/stock
source venv/bin/activate
export PYTHONPATH=/home/uamgo/stock
export JWT_SECRET_KEY=stock-secret-$(date +%s)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --log-level info
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

echo "📁 创建必要目录..."
mkdir -p /home/uamgo/stock/{data,logs}
mkdir -p /home/uamgo/nginx/www/stock

echo "📋 部署前端文件..."
cp -r frontend/* /home/uamgo/nginx/www/stock/

echo "⚙️ 配置nginx..."
cp deploy/nginx-stock.conf /home/uamgo/nginx/conf/

echo "🚀 启动服务..."
systemctl daemon-reload
systemctl enable stock-backend
systemctl start stock-backend

# 重新加载nginx
docker exec nginx nginx -s reload

echo "⏳ 等待服务启动..."
sleep 10

echo "🔍 检查服务状态..."
systemctl status stock-backend --no-pager -l
ss -tlnp | grep :8000

echo "🧪 测试API..."
curl -f http://localhost:8000/api/health 2>/dev/null && echo "✅ API健康检查通过" || echo "❌ API健康检查失败，检查日志"

echo "📋 服务信息："
echo "- 服务状态: systemctl status stock-backend"
echo "- 查看日志: journalctl -u stock-backend -f"
echo "- 重启服务: systemctl restart stock-backend"

echo "✅ 离线部署完成！"
echo "🌐 访问地址: http://stock.uamgo.com"
echo "📊 API地址: http://stock.uamgo.com/api/"

EOF

# 清理
rm offline-deploy.tar.gz

echo "🎉 离线部署完成！"
