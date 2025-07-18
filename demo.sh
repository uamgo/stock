#!/bin/bash

# Tail Trading 快速演示脚本

echo "=========================================="
echo "Tail Trading 股票交易系统 - 快速演示"
echo "=========================================="

# 检查依赖
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "错误：未找到 $1，请先安装"
        return 1
    fi
    return 0
}

echo "检查系统依赖..."
check_dependency "python3" || exit 1
check_dependency "pip3" || exit 1

echo "✓ 系统依赖检查通过"
echo ""

# 选择运行模式
echo "请选择运行模式："
echo "1. Docker模式（推荐，需要Docker）"
echo "2. 开发模式（直接运行）"
echo ""
read -p "请输入选择 [1-2]: " choice

case $choice in
    1)
        echo "启动Docker模式..."
        if check_dependency "docker" && check_dependency "docker-compose"; then
            echo "正在启动系统（这可能需要几分钟）..."
            ./start_system.sh
        else
            echo "Docker未安装，切换到开发模式..."
            choice=2
        fi
        ;;
    2)
        echo "启动开发模式..."
        ;;
    *)
        echo "无效选择，使用开发模式..."
        choice=2
        ;;
esac

if [ "$choice" = "2" ]; then
    echo "安装Python依赖..."
    cd backend
    pip3 install -r requirements.txt --quiet
    cd ..
    
    echo "启动后端服务..."
    cd backend
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    echo "等待后端启动..."
    sleep 5
    
    echo "启动前端服务..."
    cd frontend
    python3 -m http.server 3000 > /dev/null 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # 等待服务启动
    sleep 3
    
    echo ""
    echo "=========================================="
    echo "系统启动完成！"
    echo "=========================================="
    echo ""
    echo "访问地址:"
    echo "  🌐 前端界面: http://localhost:3000"
    echo "  🔧 后端API:  http://localhost:8000"
    echo "  📚 API文档:  http://localhost:8000/docs"
    echo ""
    echo "默认登录:"
    echo "  👤 用户名: admin"
    echo "  🔑 密码: admin000"
    echo ""
    echo "功能演示:"
    echo "  1. 打开浏览器访问 http://localhost:3000"
    echo "  2. 使用 admin/admin000 登录"
    echo "  3. 尝试「数据更新」功能"
    echo "  4. 尝试「股票选择」功能"
    echo "  5. 查看「定时任务」设置"
    echo ""
    echo "按 Ctrl+C 停止演示"
    
    # 清理函数
    cleanup() {
        echo ""
        echo "正在停止服务..."
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        echo "演示结束，感谢使用！"
        exit 0
    }
    
    # 捕获退出信号
    trap cleanup SIGINT SIGTERM
    
    # 等待用户中断
    wait
fi
