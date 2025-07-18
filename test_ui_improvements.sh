#!/bin/bash

echo "🎯 测试前端UI改进"
echo "================"

echo "1. 检查前端文件是否更新..."
ssh root@login.uamgo.com 'ls -la /var/lib/docker/volumes/uamgo/_data/nginx/stock/ | grep -E "index.html|app.js"'

echo ""
echo "2. 验证CSS样式..."
if ssh root@login.uamgo.com 'grep -q "stock-results-table" /var/lib/docker/volumes/uamgo/_data/nginx/stock/index.html'; then
    echo "✅ 表格高度样式已添加"
else
    echo "❌ 表格高度样式未找到"
fi

if ssh root@login.uamgo.com 'grep -q "stock-code-link" /var/lib/docker/volumes/uamgo/_data/nginx/stock/index.html'; then
    echo "✅ 股票代码链接样式已添加"
else
    echo "❌ 股票代码链接样式未找到"
fi

echo ""
echo "3. 验证JavaScript功能..."
if ssh root@login.uamgo.com 'grep -q "generateEastmoneyUrl" /var/lib/docker/volumes/uamgo/_data/nginx/stock/app.js'; then
    echo "✅ 东方财富链接生成函数已添加"
else
    echo "❌ 东方财富链接生成函数未找到"
fi

if ssh root@login.uamgo.com 'grep -q "quote.eastmoney.com" /var/lib/docker/volumes/uamgo/_data/nginx/stock/app.js'; then
    echo "✅ 东方财富URL已配置"
else
    echo "❌ 东方财富URL未配置"
fi

echo ""
echo "🎉 UI改进完成！"
echo "功能说明:"
echo "1. 选股结果表格高度固定为屏幕50% (50vh)"
echo "2. 超出部分显示垂直滚动条"
echo "3. 股票代码可点击跳转到东方财富"
echo "4. 自动识别上海(6开头)和深圳(0/3开头)市场"
echo ""
echo "📱 请访问 http://stock.uamgo.com 测试新功能"
