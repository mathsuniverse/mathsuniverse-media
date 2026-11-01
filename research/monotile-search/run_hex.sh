#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f "run_drafter.sh" > /dev/null || pgrep -f "run_more.sh" > /dev/null; do sleep 10; done
set -x
python3 sieve.py hex --nmin 7 --nmax 7 --verify sample --sample 400 --dovetail "24:8" --shape-time 120 > logs/hex2.log 2>&1
python3 regress.py kite myers > logs/regress.log 2>&1
