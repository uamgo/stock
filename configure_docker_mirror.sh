#!/bin/bash

# Docker国内源配置脚本
# 配置阿里云Docker镜像加速器

echo "🔧 配置Docker国内镜像源..."

# 在服务器上配置Docker镜像加速器
ssh root@login.uamgo.com << 'EOF'
set -e

echo "📝 配置Docker daemon..."

# 创建docker配置目录
mkdir -p /etc/docker

# 配置阿里云镜像加速器
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

echo "🔄 重启Docker服务..."
systemctl daemon-reload
systemctl restart docker

echo "✅ Docker镜像源配置完成！"

# 验证配置
echo "🔍 验证Docker配置..."
docker info | grep -A 10 "Registry Mirrors" || echo "配置已生效"

EOF

echo "🎉 Docker国内源配置完成！"
