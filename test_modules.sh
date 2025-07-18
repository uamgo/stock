#!/bin/bash
cd /home/uamgo/stock
source venv/bin/activate
echo "Testing pandas import..."
python3 -c "import pandas; print('✅ pandas import successful')"
echo "Testing akshare import..."
python3 -c "import akshare; print('✅ akshare import successful')"
echo "Testing tail_trading script..."
python3 tail_trading.py --help
