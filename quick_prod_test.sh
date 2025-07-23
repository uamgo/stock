#!/bin/bash
# 简化的生产环境测试脚本

echo "🔍 快速检查生产环境热度计算..."

# 连接生产环境并执行简单测试
ssh root@stock.uamgo.com "cd /home/uamgo/stock && .venv/bin/python -c \"
import sys
sys.path.insert(0, '/home/uamgo/stock')

try:
    from data.est.req.est_concept import EastmoneyConceptStockFetcher
    print('✅ 概念模块导入成功')
    
    fetcher = EastmoneyConceptStockFetcher()
    df = fetcher.fetch_and_save()
    
    if df is not None:
        print(f'📊 获取概念数据成功，共 {len(df)} 个概念')
        top3 = df.nlargest(3, '涨跌幅')
        print('📈 涨跌幅前3名:')
        for i, (_, row) in enumerate(top3.iterrows(), 1):
            print(f'  {i}. {row[\\\"名称\\\"]::<15} | {row[\\\"涨跌幅\\\"]:>6.2f}%')
    else:
        print('❌ 获取概念数据失败')
        
except Exception as e:
    print(f'❌ 错误: {e}')
\""
