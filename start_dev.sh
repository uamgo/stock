#!/bin/bash

# 开发环境启动脚本

echo "启动开发环境..."

# 启动后端
echo "启动后端服务..."
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 启动前端（使用Python内置服务器）
echo "启动前端服务..."
cd ../frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo ""
echo "开发环境启动完成！"
echo ""
echo "前端地址: http://localhost:3000"
echo "后端地址: http://localhost:8000"
echo "API文档:  http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待信号
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

wait
