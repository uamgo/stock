#!/bin/sh
work_dir="$( cd "$( dirname "$0" )/../" >/dev/null 2>&1 && pwd )"
echo $work_dir
export PYTHONPATH="${PYTHONPATH}:${work_dir}"
cd ${work_dir}
echo $PWD
exec python3 chat_impl.py
