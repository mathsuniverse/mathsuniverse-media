#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f "run_frontier.sh" > /dev/null; do sleep 10; done
set -x
python3 sieve.py tetrakis --nmax 12 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/tetrakis.log 2>&1
python3 sieve.py drafter --nmin 11 --nmax 13 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/drafter2.log 2>&1
python3 sieve.py kite --nmax 10 --verify sample --sample 400 --dovetail "24:8" --shape-time 240 > logs/kite.log 2>&1
python3 sieve.py hex --nmax 8 --verify sample --sample 400 --dovetail "24:8" --shape-time 120 > logs/hex.log 2>&1
python3 regress.py kite myers > logs/regress.log 2>&1
