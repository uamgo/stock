#!/bin/bash

# Tail Trading 系统管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

show_help() {
    echo "Tail Trading 系统管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start        启动系统（Docker）"
    echo "  dev          启动开发环境"
    echo "  stop         停止系统"
    echo "  restart      重启系统"
    echo "  status       查看系统状态"
    echo "  logs         查看系统日志"
    echo "  test         运行系统测试"
    echo "  clean        清理系统数据"
    echo "  update       更新系统"
    echo "  backup       备份数据"
    echo "  help         显示此帮助信息"
    echo ""
}

case "$1" in
    start)
        echo "启动Tail Trading系统..."
        ./start_system.sh
        ;;
    dev)
        echo "启动开发环境..."
        ./start_dev.sh
        ;;
    stop)
        echo "停止系统..."
        docker-compose down
        ;;
    restart)
        echo "重启系统..."
        docker-compose restart
        ;;
    status)
        echo "系统状态:"
        docker-compose ps
        ;;
    logs)
        echo "查看系统日志:"
        docker-compose logs -f --tail=100
        ;;
    test)
        echo "运行系统测试..."
        ./test_system.sh
        ;;
    clean)
        echo "清理系统数据..."
        read -p "确定要清理所有数据吗？[y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            rm -rf data/* logs/*
            echo "数据清理完成"
        fi
        ;;
    update)
        echo "更新系统..."
        git pull
        docker-compose build --no-cache
        docker-compose up -d
        ;;
    backup)
        BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
        echo "备份数据到 $BACKUP_DIR ..."
        mkdir -p "$BACKUP_DIR"
        cp -r data "$BACKUP_DIR/"
        cp -r logs "$BACKUP_DIR/"
        tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
        rm -rf "$BACKUP_DIR"
        echo "备份完成: ${BACKUP_DIR}.tar.gz"
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        echo "未知命令: $1"
        echo "使用 '$0 help' 查看帮助信息"
        exit 1
        ;;
esac
