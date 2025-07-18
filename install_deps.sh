#!/bin/bash

echo "🔧 安装项目依赖包..."

# 切换到项目目录并激活虚拟环境
cd /home/uamgo/stock
source venv/bin/activate

echo "📦 安装数据处理相关依赖..."

# 安装基础数据处理包
pip install pandas -i https://pypi.tuna.tsinghua.edu.cn/simple/ --timeout 120
pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple/ --timeout 120
pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple/ --timeout 120
pip install pandas_ta -i https://pypi.tuna.tsinghua.edu.cn/simple/ --timeout 120
pip install pymongo -i https://pypi.tuna.tsinghua.edu.cn/simple/ --timeout 120
pip install exchange_calendars -i https://pypi.tuna.tsinghua.edu.cn/simple/ --timeout 120

echo "✅ 依赖安装完成"

# 检查关键包是否安装成功
echo "🔍 验证安装..."
python -c "import pandas; print(f'pandas: {pandas.__version__}')"
python -c "import akshare; print(f'akshare: {akshare.__version__}')"
python -c "import pymongo; print('pymongo: OK')"

echo "🎯 依赖安装验证完成！"
