#!/bin/bash

# 测试国内源配置脚本

echo "🧪 测试Docker和软件源配置..."

ssh root@login.uamgo.com << 'EOF'
echo "=== Docker镜像源配置 ==="
cat /etc/docker/daemon.json 2>/dev/null || echo "Docker配置文件不存在"
echo

echo "=== Docker服务状态 ==="
systemctl status docker --no-pager -l
echo

echo "=== 测试拉取阿里云镜像 ==="
docker pull registry.cn-hangzhou.aliyuncs.com/library/python:3.11-slim
echo

echo "=== 测试pip源 ==="
docker run --rm registry.cn-hangzhou.aliyuncs.com/library/python:3.11-slim pip config list
echo

echo "✅ 测试完成！"
EOF
