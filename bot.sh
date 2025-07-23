#!/bin/bash

# 股票项目管理脚本
# 提供便捷的项目管理命令

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo "股票项目管理工具"
    echo ""
    echo "用法: $0 <命令> [选项]"
    echo ""
    echo "可用命令:"
    echo ""
    echo "开发相关:"
    echo "  dev          启动开发环境"
    echo "  install      安装依赖"
    echo "  start        启动系统"
    echo ""
    echo "部署相关:"
    echo "  deploy       本地生产部署"
    echo "  setup        环境初始化"
    echo ""
    echo "智能选股:"
    echo "  smart        智能选股（市场适应性）"
    echo "  enhanced     增强选股（放量回调+涨停逻辑）"
    echo "  select       传统选股"
    echo "  market       市场强弱分析"
    echo "  hot          热门概念分析"
    echo "  risk         连涨风险分析"
    echo "  volume       放量回调分析"
    echo "  logic        涨停逻辑分析"
    echo ""
    echo "生产环境:"
    echo "  health       生产环境健康检查"
    echo "  update       数据更新"
    echo "  monitor      性能监控"
    echo "  backup       数据备份"
    echo ""
    echo "测试相关:"
    echo "  test         运行所有测试"
    echo "  test-auth    测试认证功能"
    echo "  test-api     测试API"
    echo ""
    echo "维护相关:"
    echo "  status       检查系统状态"
    echo "  diagnose     系统诊断"
    echo "  logs         查看日志"
    echo ""
    echo "示例:"
    echo "  $0 smart     # 智能选股（推荐）"
    echo "  $0 deploy    # 执行部署"
    echo "  $0 test      # 运行测试"
}

case "$1" in
    # 开发相关
    "dev")
        echo "🚀 启动开发环境..."
        exec "$SCRIPT_DIR/scripts/development/start_dev.sh" "${@:2}"
        ;;
    "install")
        echo "📦 安装依赖..."
        exec "$SCRIPT_DIR/scripts/development/install_deps.sh" "${@:2}"
        ;;
    "start")
        echo "🔄 启动系统..."
        exec "$SCRIPT_DIR/scripts/development/start_system.sh" "${@:2}"
        ;;
    
    # 部署相关
    "deploy")
        echo "🚀 执行本地生产部署..."
        exec "$SCRIPT_DIR/deploy_local.sh" "${@:2}"
        ;;
    "setup")
        echo "⚡ 环境初始化..."
        exec "$SCRIPT_DIR/scripts/local_deploy.sh" "${@:2}"
        ;;
    
    # 智能选股相关
    "smart")
        echo "🤖 启动智能选股..."
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        OUTPUT_FILE="/Users/kevin/Downloads/smart_selection_${TIMESTAMP}.txt"
        
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            RESULT=$(source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/smart_select.py" "${@:2}")
        else
            RESULT=$(python3 "$SCRIPT_DIR/scripts/smart_select.py" "${@:2}")
        fi
        
        echo "$RESULT"
        
        # 提取股票代码并保存到文件
        STOCK_CODES=$(echo "$RESULT" | grep -o '"代码":\s*"[^"]*"' | grep -o '"[0-9]\{6\}"' | tr -d '"' | tr '\n' ',' | sed 's/,$//')
        if [ -n "$STOCK_CODES" ]; then
            echo "$STOCK_CODES" > "$OUTPUT_FILE"
            echo "💾 智能选股结果已保存到: $OUTPUT_FILE"
            echo "📋 股票代码: $STOCK_CODES"
        else
            echo "⚠️ 未找到股票代码"
        fi
        ;;
    "enhanced")
        echo "🚀 启动增强选股（放量回调+涨停逻辑）..."
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        OUTPUT_FILE="/Users/kevin/Downloads/enhanced_selection_${TIMESTAMP}.txt"
        
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            RESULT=$(source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/enhanced_select.py" "${@:2}")
        else
            RESULT=$(python3 "$SCRIPT_DIR/scripts/enhanced_select.py" "${@:2}")
        fi
        
        echo "$RESULT"
        
        # 提取股票代码并保存到文件
        STOCK_CODES=$(echo "$RESULT" | grep -o '"代码":\s*"[^"]*"' | grep -o '"[0-9]\{6\}"' | tr -d '"' | tr '\n' ',' | sed 's/,$//')
        if [ -n "$STOCK_CODES" ]; then
            echo "$STOCK_CODES" > "$OUTPUT_FILE"
            echo "💾 增强选股结果已保存到: $OUTPUT_FILE"
            echo "📋 股票代码: $STOCK_CODES"
        else
            echo "⚠️ 未找到股票代码"
        fi
        ;;
    "select")
        echo "📊 传统选股..."
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        OUTPUT_FILE="/Users/kevin/Downloads/traditional_selection_${TIMESTAMP}.txt"
        
        if [ -f "$SCRIPT_DIR/scripts/traditional_select.py" ]; then
            if [ -d "$SCRIPT_DIR/.venv" ]; then
                RESULT=$(source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/traditional_select.py" "${@:2}")
            else
                RESULT=$(python3 "$SCRIPT_DIR/scripts/traditional_select.py" "${@:2}")
            fi
        elif [ -f "$SCRIPT_DIR/tail_trading.py" ]; then
            if [ -d "$SCRIPT_DIR/.venv" ]; then
                RESULT=$(source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/tail_trading.py" select "${@:2}")
            else
                RESULT=$(python3 "$SCRIPT_DIR/tail_trading.py" select "${@:2}")
            fi
        else
            echo "❌ 选股模块未找到"
            exit 1
        fi
        
        echo "$RESULT"
        
        # 提取股票代码并保存到文件
        STOCK_CODES=$(echo "$RESULT" | grep -o '"代码":\s*"[^"]*"' | grep -o '"[0-9]\{6\}"' | tr -d '"' | tr '\n' ',' | sed 's/,$//')
        if [ -n "$STOCK_CODES" ]; then
            echo "$STOCK_CODES" > "$OUTPUT_FILE"
            echo "💾 传统选股结果已保存到: $OUTPUT_FILE"
            echo "📋 股票代码: $STOCK_CODES"
        else
            echo "⚠️ 未找到股票代码"
        fi
        ;;
    "market")
        echo "📊 市场强弱分析..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/real_market_analyzer.py" "${@:2}"
        else
            python3 "$SCRIPT_DIR/scripts/real_market_analyzer.py" "${@:2}"
        fi
        ;;
    "hot")
        echo "🔥 热门概念分析..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/hot_concept_analyzer.py" "${@:2}"
        else
            python3 "$SCRIPT_DIR/scripts/hot_concept_analyzer.py" "${@:2}"
        fi
        ;;
    "risk")
        echo "⚠️ 连涨风险分析..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/consecutive_rise_analyzer.py" "${@:2}"
        else
            python3 "$SCRIPT_DIR/scripts/consecutive_rise_analyzer.py" "${@:2}"
        fi
        ;;
    "volume")
        echo "📈 放量回调分析..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/volume_retracement_analyzer.py" "${@:2}"
        else
            python3 "$SCRIPT_DIR/scripts/volume_retracement_analyzer.py" "${@:2}"
        fi
        ;;
    "logic")
        echo "🎯 涨停逻辑分析..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/limit_up_logic_analyzer.py" "${@:2}"
        else
            python3 "$SCRIPT_DIR/scripts/limit_up_logic_analyzer.py" "${@:2}"
        fi
        ;;
    
    # 测试相关
    "test")
        echo "🧪 运行所有测试..."
        exec "$SCRIPT_DIR/scripts/testing/test_all_auth.sh" "${@:2}"
        ;;
    "test-auth")
        echo "🔐 测试认证功能..."
        exec "$SCRIPT_DIR/scripts/testing/test_all_auth.sh" "${@:2}"
        ;;
    "test-api")
        echo "🌐 测试API..."
        exec "$SCRIPT_DIR/scripts/testing/test_api.sh" "${@:2}"
        ;;
    
    # 维护相关
    "status")
        echo "📊 检查系统状态..."
        exec "$SCRIPT_DIR/scripts/maintenance/check_status.sh" "${@:2}"
        ;;
    "diagnose")
        echo "🔍 系统诊断..."
        if [ -f "$SCRIPT_DIR/scripts/maintenance/diagnose_local.sh" ]; then
            exec "$SCRIPT_DIR/scripts/maintenance/diagnose_local.sh" "${@:2}"
        else
            exec "$SCRIPT_DIR/scripts/maintenance/diagnose.sh" "${@:2}"
        fi
        ;;
    "logs")
        echo "📝 查看日志..."
        if [ -f "$SCRIPT_DIR/scripts/maintenance/check_status.sh" ]; then
            "$SCRIPT_DIR/scripts/maintenance/check_status.sh" logs
        else
            echo "日志查看脚本不存在"
            exit 1
        fi
        ;;
    
    # 生产环境相关
    "health")
        echo "🏥 生产环境健康检查..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/production_health_check.py" "${@:2}"
        else
            python3 "$SCRIPT_DIR/scripts/production_health_check.py" "${@:2}"
        fi
        ;;
    "update")
        echo "🔄 数据更新..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/production_data_updater.py" "${@:2}"
        else
            python3 "$SCRIPT_DIR/scripts/production_data_updater.py" "${@:2}"
        fi
        ;;
    "monitor")
        echo "📊 性能监控..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate" && python3 "$SCRIPT_DIR/scripts/performance_monitor.py" "${@:2}"
        else
            python3 "$SCRIPT_DIR/scripts/performance_monitor.py" "${@:2}"
        fi
        ;;
    "backup")
        echo "💾 数据备份..."
        echo "执行数据备份任务..."
        
        # 创建备份目录
        BACKUP_DIR="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M)"
        mkdir -p "$BACKUP_DIR"
        
        # 备份数据文件
        if [ -d "/tmp/stock" ]; then
            echo "备份数据到: $BACKUP_DIR"
            tar -czf "$BACKUP_DIR/stock_data_$(date +%Y%m%d_%H%M).tar.gz" -C /tmp stock/ 2>/dev/null
            echo "✅ 数据备份完成"
        else
            echo "⚠️ 数据目录不存在，跳过备份"
        fi
        
        # 备份配置文件
        if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
            cp "$SCRIPT_DIR/requirements.txt" "$BACKUP_DIR/"
        fi
        
        echo "💾 备份完成: $BACKUP_DIR"
        ;;
    
    # 帮助
    "help"|"-h"|"--help"|"")
        show_help
        ;;
    
    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
