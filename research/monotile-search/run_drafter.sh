#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f "run_rest.sh" > /dev/null || pgrep -f "run_more.sh" > /dev/null; do sleep 10; done
set -x
python3 sieve.py drafter --nmin 14 --nmax 15 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/drafter3.log 2>&1
