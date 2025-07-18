#!/bin/bash

# 检查服务器Docker状态和可用镜像
SERVER="root@login.uamgo.com"

echo "🔍 检查服务器Docker状态..."

ssh $SERVER << 'EOF'
echo "=== Docker 版本 ==="
docker --version

echo -e "\n=== Docker 服务状态 ==="
systemctl status docker --no-pager -l

echo -e "\n=== 当前镜像 ==="
docker images

echo -e "\n=== 测试镜像拉取 ==="
echo "测试Ubuntu镜像..."
docker pull ubuntu:22.04 || echo "Ubuntu镜像拉取失败"

echo -e "\n测试Alpine镜像..."
docker pull alpine:latest || echo "Alpine镜像拉取失败"

echo -e "\n=== 网络连接测试 ==="
echo "测试Docker Hub连接..."
curl -I https://registry-1.docker.io/v2/ || echo "Docker Hub连接失败"

echo -e "\n测试阿里云镜像连接..."
curl -I https://registry.cn-hangzhou.aliyuncs.com/v2/ || echo "阿里云镜像连接失败"

echo -e "\n=== Docker配置 ==="
cat /etc/docker/daemon.json 2>/dev/null || echo "没有daemon.json配置文件"

EOF
