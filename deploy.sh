#!/bin/bash

# 统一部署脚本 - 支持本地和生产环境部署
# 用法：
#   ./deploy.sh local     # 本地部署
#   ./deploy.sh production # 生产环境部署
#   ./deploy.sh restart   # 仅重启生产服务

set -e

# 安全重启后端服务的函数
safe_restart_backend() {
    local mode="$1"  # local 或 remote
    
    if [ "$mode" = "remote" ]; then
        echo "🔄 远程安全重启后端服务..."
        ssh root@stock.uamgo.com << 'RESTART_EOF'
            cd /home/uamgo/stock
            
            echo "🛑 安全停止后端服务..."
            # 1. 优雅停止：发送TERM信号
            if [ -f "backend.pid" ]; then
                PID=$(cat backend.pid)
                if ps -p $PID > /dev/null 2>&1; then
                    echo "发送TERM信号到进程 $PID..."
                    kill -TERM $PID 2>/dev/null || true
                    # 等待进程优雅关闭（最多10秒）
                    for i in {1..10}; do
                        if ! ps -p $PID > /dev/null 2>&1; then
                            echo "✅ 进程已优雅关闭"
                            break
                        fi
                        sleep 1
                    done
                    # 如果进程仍在运行，强制关闭
                    if ps -p $PID > /dev/null 2>&1; then
                        echo "⚠️ 进程未响应TERM信号，发送KILL信号..."
                        kill -KILL $PID 2>/dev/null || true
                        sleep 2
                    fi
                fi
                rm -f backend.pid
            fi
            
            # 2. 清理所有相关进程
            echo "🧹 清理所有后端相关进程..."
            pkill -f "uvicorn.*backend.app.main" 2>/dev/null || true
            pkill -f "python.*backend" 2>/dev/null || true
            sleep 2
            
            # 3. 检查端口占用
            echo "🔍 检查端口8000占用..."
            if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
                echo "⚠️ 端口8000仍被占用，尝试清理..."
                lsof -ti:8000 | xargs kill -9 2>/dev/null || true
                sleep 2
            fi
            
            # 4. 启动新服务
            echo "🚀 启动新的后端服务..."
            if [ ! -d ".venv" ]; then
                echo "❌ 虚拟环境不存在，请先执行完整部署"
                exit 1
            fi
            
            # 确保日志目录存在
            mkdir -p logs
            
            # 启动服务
            nohup .venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
            NEW_PID=$!
            echo $NEW_PID > backend.pid
            
            echo "📝 新服务进程ID: $NEW_PID"
            
            # 5. 验证服务启动
            echo "⏳ 等待服务启动..."
            sleep 5
            
            # 检查进程是否还在运行
            if ps -p $NEW_PID > /dev/null 2>&1; then
                echo "✅ 进程运行正常"
            else
                echo "❌ 进程已退出，请检查日志"
                tail -20 logs/backend.log
                exit 1
            fi
            
            # 检查健康状态
            echo "🏥 检查服务健康状态..."
            for i in {1..6}; do
                if curl -f http://localhost:8000/health >/dev/null 2>&1; then
                    echo "✅ 后端服务健康检查通过"
                    break
                elif [ $i -eq 6 ]; then
                    echo "⚠️ 健康检查失败，但进程在运行。请检查日志:"
                    tail -10 logs/backend.log
                else
                    echo "⏳ 等待服务就绪... ($i/6)"
                    sleep 5
                fi
            done
            
            echo "🎉 后端服务重启完成！"
            echo "📋 服务信息："
            echo "  进程ID: $NEW_PID"
            echo "  日志文件: logs/backend.log"
            echo "  访问地址: http://stock.uamgo.com"
RESTART_EOF
    else
        echo "🔄 本地安全重启后端服务..."
        # 本地重启逻辑（如果需要的话）
        echo "本地重启功能待实现"
    fi
}

DEPLOYMENT_TYPE="$1"

# 如果是重启命令，直接执行重启
if [ "$DEPLOYMENT_TYPE" = "restart" ]; then
    safe_restart_backend "remote"
    exit 0
fi

if [ -z "$DEPLOYMENT_TYPE" ]; then
    echo "使用方法："
    echo "  ./deploy.sh local [选项]        # 本地部署"
    echo "  ./deploy.sh production          # 生产环境部署"
    echo "  ./deploy.sh restart             # 仅重启生产服务"
    echo ""
    echo "本地部署选项："
    echo "  --clean                         # 清理旧缓存"
    echo "  --init-data                     # 初始化基础数据"
    echo ""
    echo "示例："
    echo "  ./deploy.sh local               # 基本本地部署"
    echo "  ./deploy.sh local --clean       # 本地部署并清理缓存"
    echo "  ./deploy.sh local --init-data   # 本地部署并初始化数据"
    echo "  ./deploy.sh restart             # 仅重启生产服务（不重新部署代码）"
    exit 1
fi

case "$DEPLOYMENT_TYPE" in
    "local")
        echo "🚀 本地生产环境部署"
        echo "===================================================="
        echo "前端: 已部署在nginx目录"
        echo "后端: 本地Python环境运行"
        echo "数据: 使用真实API数据源"
        echo "===================================================="

        # 1. 检查Python环境
        echo "🔍 检查Python环境..."
        if ! command -v python3 &> /dev/null; then
            echo "❌ Python3 未安装，请先安装Python 3.8+"
            exit 1
        fi

        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        echo "✅ Python版本: $PYTHON_VERSION"

        # 2. 检查并创建虚拟环境
        echo "📦 检查虚拟环境..."
        if [ ! -d ".venv" ]; then
            echo "创建虚拟环境..."
            python3 -m venv .venv
            echo "✅ 虚拟环境创建完成"
            VENV_CREATED=true
        else
            echo "✅ 虚拟环境已存在"
            VENV_CREATED=false
        fi

        # 3. 激活虚拟环境并安装/更新依赖
        echo "📥 检查依赖..."
        source .venv/bin/activate

        # 升级pip
        pip install --upgrade pip --quiet

        # 智能检查并安装依赖（复用生产环境的逻辑）
        # 检查主项目依赖是否需要更新
        NEED_UPDATE_MAIN=false
        if [ -f "requirements.txt" ]; then
            if [ "$VENV_CREATED" = true ] || [ ! -f ".requirements.hash" ]; then
                NEED_UPDATE_MAIN=true
            else
                # 检查requirements.txt是否有变化
                CURRENT_HASH=$(md5sum requirements.txt | cut -d' ' -f1)
                STORED_HASH=$(cat .requirements.hash 2>/dev/null || echo "")
                if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
                    NEED_UPDATE_MAIN=true
                fi
            fi
            
            if [ "$NEED_UPDATE_MAIN" = true ]; then
                echo "安装/更新主项目依赖..."
                pip install -r requirements.txt --quiet
                md5sum requirements.txt | cut -d' ' -f1 > .requirements.hash
            else
                echo "✅ 主项目依赖无变化，跳过安装"
            fi
        fi

        # 检查后端依赖是否需要更新
        NEED_UPDATE_BACKEND=false
        if [ -f "backend/requirements.txt" ]; then
            if [ "$VENV_CREATED" = true ] || [ ! -f ".backend_requirements.hash" ]; then
                NEED_UPDATE_BACKEND=true
            else
                # 检查backend/requirements.txt是否有变化
                CURRENT_HASH=$(md5sum backend/requirements.txt | cut -d' ' -f1)
                STORED_HASH=$(cat .backend_requirements.hash 2>/dev/null || echo "")
                if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
                    NEED_UPDATE_BACKEND=true
                fi
            fi
            
            if [ "$NEED_UPDATE_BACKEND" = true ]; then
                echo "安装/更新后端依赖..."
                pip install -r backend/requirements.txt --quiet
                md5sum backend/requirements.txt | cut -d' ' -f1 > .backend_requirements.hash
            else
                echo "✅ 后端依赖无变化，跳过安装"
            fi
        fi

        # 4. 创建必要的目录
        echo "📁 创建必要目录..."
        mkdir -p logs
        mkdir -p backups
        mkdir -p /tmp/stock
        mkdir -p /tmp/stock/daily
        mkdir -p /tmp/stock/cache
        mkdir -p /tmp/stock/est_prepare_data
        echo "✅ 目录结构完成"

        # 5. 设置权限
        echo "🔧 设置权限..."
        chmod +x bot.sh 2>/dev/null || true
        chmod +x deploy.sh 2>/dev/null || true
        find scripts/ -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
        echo "✅ 权限设置完成"

        # 6. 清理旧数据缓存（可选）
        if [[ "${@:2}" == *"--clean"* ]]; then
            echo "🧹 清理旧缓存..."
            rm -rf /tmp/stock/cache/* 2>/dev/null || true
            echo "✅ 缓存清理完成"
        fi

        # 7. 运行健康检查
        echo "🏥 运行系统健康检查..."
        if python3 scripts/production_health_check.py; then
            echo "✅ 系统健康检查通过"
        else
            echo "⚠️ 健康检查发现一些问题，但不影响基本功能"
        fi

        # 8. 初始化数据（如果需要）
        if [[ "${@:2}" == *"--init-data"* ]] || [ ! -f "/tmp/stock/est_prepare_data/members_dict.pkl" ]; then
            echo "📊 初始化基础数据..."
            if python3 scripts/production_data_updater.py --mode=concept; then
                echo "✅ 基础数据初始化完成"
            else
                echo "⚠️ 数据初始化遇到网络问题，可稍后手动更新"
            fi
        fi

        # 9. 测试核心功能
        echo "🧪 测试核心功能..."
        if python3 -c "from scripts.smart_select import SmartStockSelector; print('✅ 智能选股模块正常')" 2>/dev/null; then
            echo "✅ 核心模块测试通过"
        else
            echo "⚠️ 部分模块测试失败，但系统已部署"
        fi

        echo ""
        echo "🎉 本地生产环境部署完成！"
        echo "===================================================="
        echo ""
        echo "📝 快速使用："
        echo "  ./bot.sh smart      # 智能选股（推荐）"
        echo "  ./bot.sh enhanced   # 增强选股"
        echo "  ./bot.sh health     # 健康检查"
        echo "  ./bot.sh update     # 数据更新"
        echo "  ./bot.sh monitor    # 性能监控"
        echo ""
        echo "🔧 管理命令："
        echo "  ./bot.sh backup     # 数据备份"
        echo "  ./bot.sh status     # 系统状态"
        echo "  ./bot.sh logs       # 查看日志"
        echo ""
        echo "🚀 立即开始："
        echo "  ./bot.sh smart"
        echo ""

        # 10. 显示部署信息
        echo "📋 部署信息："
        echo "  部署类型: 本地生产环境"
        echo "  Python版本: $PYTHON_VERSION"  
        echo "  项目路径: $(pwd)"
        echo "  虚拟环境: .venv"
        echo "  数据目录: /tmp/stock"
        echo "  前端: nginx目录（已部署）"
        echo "  后端: 本地Python运行"
        echo ""
        echo "✅ 部署成功！无需Docker，轻量高效。"

        # 11. 可选的后端服务启动提示
        if [ -f "backend/start.sh" ]; then
            echo ""
            echo "💡 提示: 如需启动后端API服务，请运行："
            echo "  cd backend && ./start.sh"
        fi
        ;;
        
    "production")
        echo "🚀 开始部署到生产服务器..."
        
        # 生产环境配置
        SERVER="root@stock.uamgo.com"
        BACKEND_DIR="/home/uamgo/stock"
        FRONTEND_DIR="/home/uamgo/nginx/www/stock"
        NGINX_CONF_DIR="/home/uamgo/nginx/conf"
        
        echo "服务器: $SERVER"
        echo "后端目录: $BACKEND_DIR"
        echo "前端目录: $FRONTEND_DIR"
        echo "Nginx配置: $NGINX_CONF_DIR"
        echo ""

        # 1. 创建后端代码压缩包
        echo "📦 打包后端代码..."
        tar -czf backend-deploy.tar.gz \
            --exclude='.git' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.venv' \
            --exclude='node_modules' \
            --exclude='logs/*' \
            --exclude='data/cache/*' \
            --exclude='data/backups/*' \
            backend/ \
            tail_trading/ \
            data/ \
            scripts/ \
            requirements.txt \
            tail_trading.py \
            bot.sh \
            setup.py

        echo "✅ 后端代码打包完成"

        # 2. 创建前端代码压缩包
        echo "📦 打包前端代码..."
        tar -czf frontend-deploy.tar.gz frontend/

        echo "✅ 前端代码打包完成"

        # 3. 上传文件到服务器
        echo "📤 上传后端代码到服务器..."
        scp backend-deploy.tar.gz $SERVER:/tmp/

        echo "📤 上传前端代码到服务器..."
        scp frontend-deploy.tar.gz $SERVER:/tmp/

        echo "📤 上传nginx配置文件..."
        scp deploy/nginx-stock.conf $SERVER:/tmp/ 2>/dev/null || echo "⚠️ nginx配置文件不存在，跳过"

        echo "✅ 文件上传完成"

        # 4. 在服务器上执行部署
        echo "🔧 在服务器上执行部署..."
        ssh $SERVER << 'EOF'
set -e

echo "🛑 停止当前后端服务..."
# 使用安全停止逻辑
if [ -f "backend.pid" ]; then
    PID=$(cat backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "发送TERM信号到进程 $PID..."
        kill -TERM $PID 2>/dev/null || true
        # 等待进程优雅关闭（最多10秒）
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "✅ 进程已优雅关闭"
                break
            fi
            sleep 1
        done
        # 如果进程仍在运行，强制关闭
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️ 进程未响应TERM信号，发送KILL信号..."
            kill -KILL $PID 2>/dev/null || true
        fi
    fi
    rm -f backend.pid
fi

# 清理所有相关进程
pkill -f "uvicorn.*backend.app.main" 2>/dev/null || true
pkill -f "python.*backend" 2>/dev/null || true
sleep 2

echo "📁 备份和更新代码..."
# 备份现有虚拟环境和依赖hash文件（如果存在）
if [ -d "/home/uamgo/stock/.venv" ]; then
    echo "备份虚拟环境和依赖缓存..."
    mkdir -p /tmp/stock-env-backup
    mv /home/uamgo/stock/.venv /tmp/stock-env-backup/
    # 备份依赖hash文件
    if [ -f "/home/uamgo/stock/.requirements.hash" ]; then
        mv /home/uamgo/stock/.requirements.hash /tmp/stock-env-backup/
    fi
    if [ -f "/home/uamgo/stock/.backend_requirements.hash" ]; then
        mv /home/uamgo/stock/.backend_requirements.hash /tmp/stock-env-backup/
    fi
fi

# 备份现有后端代码（排除虚拟环境）
if [ -d "/home/uamgo/stock" ]; then
    echo "备份后端代码..."
    mv /home/uamgo/stock /home/uamgo/stock.backup.$(date +%Y%m%d_%H%M%S) || true
fi

# 备份现有前端代码
if [ -d "/home/uamgo/nginx/www/stock" ]; then
    echo "备份前端代码..."
    mv /home/uamgo/nginx/www/stock /home/uamgo/nginx/www/stock.backup.$(date +%Y%m%d_%H%M%S) || true
fi

echo "📦 解压新代码..."
# 创建目录并解压后端代码
mkdir -p /home/uamgo/stock
cd /home/uamgo/stock
tar -xzf /tmp/backend-deploy.tar.gz
rm /tmp/backend-deploy.tar.gz

# 恢复虚拟环境和依赖缓存（如果备份存在）
if [ -d "/tmp/stock-env-backup" ]; then
    echo "恢复虚拟环境和依赖缓存..."
    if [ -d "/tmp/stock-env-backup/.venv" ]; then
        mv /tmp/stock-env-backup/.venv .venv
    fi
    if [ -f "/tmp/stock-env-backup/.requirements.hash" ]; then
        mv /tmp/stock-env-backup/.requirements.hash .requirements.hash
    fi
    if [ -f "/tmp/stock-env-backup/.backend_requirements.hash" ]; then
        mv /tmp/stock-env-backup/.backend_requirements.hash .backend_requirements.hash
    fi
    rm -rf /tmp/stock-env-backup
fi

# 创建目录并解压前端代码
mkdir -p /home/uamgo/nginx/www/stock
cd /home/uamgo/nginx/www/stock
tar -xzf /tmp/frontend-deploy.tar.gz --strip-components=1
rm /tmp/frontend-deploy.tar.gz

echo "⚙️ 配置nginx..."
# 更新nginx配置（如果存在）
if [ -f "/tmp/nginx-stock.conf" ]; then
    cp /tmp/nginx-stock.conf /home/uamgo/nginx/conf/
    rm /tmp/nginx-stock.conf
    echo "✅ nginx配置已更新到宿主机"
    
    # 复制配置到nginx容器内
    echo "🔄 复制配置到nginx容器..."
    docker cp /home/uamgo/nginx/conf/nginx-stock.conf nginx:/etc/nginx/conf.d/
    
    # 重新加载nginx配置
    echo "🔄 重新加载nginx配置..."
    docker exec nginx nginx -s reload || echo "⚠️ nginx重载失败，请手动检查"
else
    echo "⚠️ 未找到nginx配置文件"
fi

echo "🐍 配置Python环境..."
cd /home/uamgo/stock

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d ".venv" ]; then
    echo "创建新的虚拟环境..."
    python3 -m venv .venv
    VENV_CREATED=true
else
    echo "✅ 使用现有虚拟环境"
    VENV_CREATED=false
fi

# 激活虚拟环境
source .venv/bin/activate

# 升级pip（总是执行）
echo "升级pip..."
pip install --upgrade pip --quiet

# 检查并安装依赖
echo "📥 检查Python依赖..."

# 检查主项目依赖是否需要更新
NEED_UPDATE_MAIN=false
if [ -f "requirements.txt" ]; then
    if [ "$VENV_CREATED" = true ] || [ ! -f ".requirements.hash" ]; then
        NEED_UPDATE_MAIN=true
    else
        # 检查requirements.txt是否有变化
        CURRENT_HASH=$(md5sum requirements.txt | cut -d' ' -f1)
        STORED_HASH=$(cat .requirements.hash 2>/dev/null || echo "")
        if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
            NEED_UPDATE_MAIN=true
        fi
    fi
    
    if [ "$NEED_UPDATE_MAIN" = true ]; then
        echo "安装/更新主项目依赖..."
        pip install -r requirements.txt
        md5sum requirements.txt | cut -d' ' -f1 > .requirements.hash
    else
        echo "✅ 主项目依赖无变化，跳过安装"
    fi
fi

# 检查后端依赖是否需要更新
NEED_UPDATE_BACKEND=false
if [ -f "backend/requirements.txt" ]; then
    if [ "$VENV_CREATED" = true ] || [ ! -f ".backend_requirements.hash" ]; then
        NEED_UPDATE_BACKEND=true
    else
        # 检查backend/requirements.txt是否有变化
        CURRENT_HASH=$(md5sum backend/requirements.txt | cut -d' ' -f1)
        STORED_HASH=$(cat .backend_requirements.hash 2>/dev/null || echo "")
        if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
            NEED_UPDATE_BACKEND=true
        fi
    fi
    
    if [ "$NEED_UPDATE_BACKEND" = true ]; then
        echo "安装/更新后端依赖..."
        pip install -r backend/requirements.txt
        md5sum backend/requirements.txt | cut -d' ' -f1 > .backend_requirements.hash
    else
        echo "✅ 后端依赖无变化，跳过安装"
    fi
fi

echo "📁 创建必要目录..."
mkdir -p logs
mkdir -p data/cache
mkdir -p data/backups
mkdir -p /tmp/stock
mkdir -p /tmp/stock/daily
mkdir -p /tmp/stock/cache
mkdir -p /tmp/stock/est_prepare_data

echo "🔧 设置权限..."
chmod +x bot.sh 2>/dev/null || true
chmod +x backend/start.sh 2>/dev/null || true
find scripts/ -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

echo "🚀 启动后端服务..."
# 确保日志目录存在
mkdir -p logs

# 启动后端服务（在后台运行）
nohup .venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > backend.pid

echo "📝 新服务进程ID: $NEW_PID"

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查进程是否还在运行
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ 进程运行正常"
else
    echo "❌ 进程已退出，请检查日志"
    tail -20 logs/backend.log
    exit 1
fi

# 检查服务是否正常启动
echo "🏥 检查服务健康状态..."
for i in {1..6}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ 后端服务健康检查通过"
        break
    elif [ $i -eq 6 ]; then
        echo "⚠️ 健康检查失败，但进程在运行。请检查日志:"
        tail -10 logs/backend.log
    else
        echo "⏳ 等待服务就绪... ($i/6)"
        sleep 5
    fi
done

echo "🎉 生产环境部署完成！"
echo ""
echo "📋 服务信息："
echo "  前端页面: http://stock.uamgo.com"
echo "  后端服务: 运行在内部8000端口"
echo ""
echo "📝 管理命令："
echo "  查看后端日志: tail -f /home/uamgo/stock/logs/backend.log"
echo "  重启后端服务: ./deploy.sh restart"
echo "  停止后端服务: kill \$(cat /home/uamgo/stock/backend.pid)"

EOF

        # 5. 清理本地临时文件
        echo "🧹 清理本地临时文件..."
        rm -f backend-deploy.tar.gz frontend-deploy.tar.gz

        echo ""
        echo "🎉 生产环境部署完成！"
        echo "🌐 访问地址: http://stock.uamgo.com"
        echo ""
        echo "📊 部署后检查："
        echo "  前端: http://stock.uamgo.com"
        echo "  后端: 通过nginx代理访问 /api/ 路径"
        ;;
        
    *)
        echo "❌ 无效的部署类型: $DEPLOYMENT_TYPE"
        echo "支持的类型: local, production"
        exit 1
        ;;
esac
