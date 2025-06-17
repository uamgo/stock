#!/bin/bash

# 获取当前脚本所在目录的上一层作为 base dir
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Base dir: $BASE_DIR"
# 添加每周执行一次的 crontab 任务，同步所有股票代码
CRON_JOB_CODES="0 3 * * 0 python3 $BASE_DIR/data/sync_all_codes.py"
CRON_JOB_CONCEPT="0 3 * * 0 python3 $BASE_DIR/data/sync_concept.py"
(crontab -l 2>/dev/null; echo "$CRON_JOB_CODES"; echo "$CRON_JOB_CONCEPT") | sort | uniq | crontab -
echo "Crontab job added: $CRON_JOB_CODES"
echo "Crontab job added: $CRON_JOB_CONCEPT"

# 添加每天执行一次的 crontab 任务，同步所有股票的日线数据
CRON_JOB_DAILY="0 23 * * * python3 $BASE_DIR/data/sync_daily_hist.py"
(crontab -l 2>/dev/null; echo "$CRON_JOB_DAILY") | sort | uniq | crontab -
echo "Crontab job added: $CRON_JOB_DAILY"

# 添加每分钟执行一次的 crontab 任务，同步所有股票的分钟数据
CRON_JOB_MINUTE="30 * * * * python3 $BASE_DIR/data/sync_minute.py"
(crontab -l 2>/dev/null; echo "$CRON_JOB_MINUTE") | sort | uniq | crontab -
echo "Crontab job added: $CRON_JOB_MINUTE"