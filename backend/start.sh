#!/bin/bash

# Tail Trading 后端启动脚本

echo "启动 Tail Trading 后端服务..."

# 检查是否在正确的目录
if [ ! -f "requirements.txt" ]; then
    echo "错误：请在backend目录中运行此脚本"
    exit 1
fi

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3"
    exit 1
fi

# 安装依赖
echo "安装Python依赖..."
pip3 install -r requirements.txt

# 创建必要的目录
mkdir -p data
mkdir -p logs

# 启动服务
echo "启动FastAPI服务..."
echo "API文档地址: http://localhost:8000/docs"
echo "管理界面地址: http://localhost:8000/"
echo ""
echo "默认登录用户:"
echo "用户名: admin"
echo "密码: admin000"
echo ""
echo "按 Ctrl+C 停止服务"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
