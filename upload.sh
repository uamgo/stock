#!/bin/bash

# 简单上传脚本
echo "📦 创建部署包..."
tar -czf stock-deploy.tar.gz \
    backend/ \
    tail_trading/ \
    frontend/ \
    data/ \
    Dockerfile.backend \
    deploy/nginx-stock.conf \
    tail_trading.py \
    requirements.txt

echo "📤 上传到服务器..."
scp stock-deploy.tar.gz root@login.uamgo.com:/tmp/

echo "🧹 清理本地文件..."
rm stock-deploy.tar.gz

echo "✅ 上传完成！"
echo "现在请登录服务器执行部署："
echo "ssh root@login.uamgo.com"
echo "然后按照 MANUAL_DEPLOY.md 中的步骤操作"
