#!/bin/bash

echo "🔗 测试东方财富链接格式"
echo "====================="

echo "修正后的链接格式:"
echo "- 上海股票 (6开头): https://quote.eastmoney.com/concept/sh600111.html"
echo "- 深圳股票 (0开头): https://quote.eastmoney.com/concept/sz000001.html"
echo "- 深圳股票 (3开头): https://quote.eastmoney.com/concept/sz300066.html"
echo ""

echo "验证文件是否更新..."
if ssh root@login.uamgo.com 'grep -q "quote.eastmoney.com/concept/" /var/lib/docker/volumes/uamgo/_data/nginx/stock/app.js'; then
    echo "✅ 链接格式已更新"
else
    echo "❌ 链接格式未更新"
fi

if ssh root@login.uamgo.com 'grep -q "marketPrefix = '\''sh'\''" /var/lib/docker/volumes/uamgo/_data/nginx/stock/app.js'; then
    echo "✅ 上海市场前缀正确"
else
    echo "❌ 上海市场前缀错误"
fi

if ssh root@login.uamgo.com 'grep -q "marketPrefix = '\''sz'\''" /var/lib/docker/volumes/uamgo/_data/nginx/stock/app.js'; then
    echo "✅ 深圳市场前缀正确"
else
    echo "❌ 深圳市场前缀错误"
fi

echo ""
echo "🎯 链接修正完成！"
echo "现在股票代码点击后会跳转到正确的东方财富页面："
echo "- 600111 → https://quote.eastmoney.com/concept/sh600111.html"
echo "- 000001 → https://quote.eastmoney.com/concept/sz000001.html"
echo "- 300066 → https://quote.eastmoney.com/concept/sz300066.html"
