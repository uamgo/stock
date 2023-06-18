#!/bin/sh
work_dir="$( cd "$( dirname "$0" )/../" >/dev/null 2>&1 && pwd )"
export PYTHONPATH="${PYTHONPATH}:${work_dir}";cd ${work_dir};exec python3 chat_impl.py