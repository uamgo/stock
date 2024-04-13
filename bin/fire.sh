#!/bin/sh
python3 -m cProfile -o /tmp/stock.prof right.py
flameprof /tmp/stock.prof >/tmp/stock.svg
# then open browser
