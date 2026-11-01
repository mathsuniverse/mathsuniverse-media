#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f "run_rest.sh" > /dev/null || pgrep -f "run_frontier.sh" > /dev/null; do sleep 10; done
set -x
python3 sieve.py floret --nmin 8 --nmax 9 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/floret2.log 2>&1
python3 sieve.py tetrakis --nmin 13 --nmax 14 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/tetrakis2.log 2>&1
