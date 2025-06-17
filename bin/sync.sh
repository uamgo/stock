#!/bin/bash

# 获取当前脚本所在目录的上一层作为 base dir
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

scp -r "$BASE_DIR/bin" "$BASE_DIR/data" root@code.uamgo.com:/root/stock