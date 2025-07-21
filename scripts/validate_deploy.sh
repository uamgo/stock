#!/bin/bash

# 部署脚本验证工具

echo "🔍 验证部署脚本完整性..."

# 检查主部署脚本
if [ -f "deploy.sh" ]; then
    echo "✅ deploy.sh 存在"
    if [ -x "deploy.sh" ]; then
        echo "✅ deploy.sh 可执行"
    else
        echo "❌ deploy.sh 不可执行"
    fi
else
    echo "❌ deploy.sh 不存在"
fi

# 检查旧文件是否已清理
echo ""
echo "🧹 检查旧文件清理情况..."

if [ -f "deploy_local.sh" ]; then
    echo "⚠️ deploy_local.sh 仍然存在，应该被删除"
else
    echo "✅ deploy_local.sh 已清理"
fi

if [ -f "deploy_production.sh" ]; then
    echo "⚠️ deploy_production.sh 仍然存在，应该被删除"
else
    echo "✅ deploy_production.sh 已清理"
fi

# 测试部署脚本语法
echo ""
echo "🔧 测试部署脚本语法..."
if bash -n deploy.sh; then
    echo "✅ deploy.sh 语法正确"
else
    echo "❌ deploy.sh 语法错误"
fi

# 测试使用帮助
echo ""
echo "📖 测试使用帮助..."
echo "--- 部署脚本帮助信息 ---"
./deploy.sh
echo "--- 帮助信息结束 ---"

echo ""
echo "🎉 验证完成！"
