#!/bin/sh

# Clone the repository
git clone https://github.com/uamgo/stock.git stock
cd stock
git pull -r origin main

# Set pip configuration
pip3 config set install.trusted-host mirrors.aliyun.com
pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple

# Create or clear the installed.txt file
> /app/installed.txt

# Install required packages if not already installed
while IFS= read -r package; do
  if pip3 show "$package" > /dev/null 2>&1; then
    echo "$package" >> /app/installed.txt
  else
    pip3 install "$package"
  fi
done < requirements.txt

# Run the application
python stock_ui.py