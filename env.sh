#!/bin/bash
# 获取当前脚本所在的目录路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR"