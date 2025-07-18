#!/bin/bash

# Tail Trading 系统快速启动脚本

set -e

echo "=========================================="
echo "Tail Trading 股票交易系统"
echo "=========================================="

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "错误：未安装Docker，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误：未安装docker-compose，请先安装docker-compose"
    exit 1
fi

# 创建必要的目录
mkdir -p data logs

# 设置权限
chmod -R 755 data logs

echo "正在构建Docker镜像..."
docker-compose build

echo "正在启动服务..."
docker-compose up -d

echo ""
echo "=========================================="
echo "服务启动完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端界面: http://localhost"
echo "  后端API:  http://localhost:8000"
echo "  API文档:  http://localhost:8000/docs"
echo ""
echo "默认登录用户:"
echo "  用户名: admin"
echo "  密码: admin000"
echo ""
echo "查看服务状态: docker-compose ps"
echo "查看服务日志: docker-compose logs -f"
echo "停止服务:     docker-compose down"
echo ""
echo "=========================================="
