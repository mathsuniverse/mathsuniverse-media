#!/bin/bash
# Regression stage: Myers grids then kite (stage-1 caps), then regress.py
cd "$(dirname "$0")"
set -x
# done: python3 sieve.py square --nmax 8 --verify all --dovetail "24:8" --shape-time 120 > logs/square.log 2>&1
python3 sieve.py tri --nmax 10 --verify all --dovetail "24:8" --shape-time 120 > logs/tri.log 2>&1
python3 sieve.py hex --nmax 8 --verify sample --sample 400 --dovetail "24:8" --shape-time 120 > logs/hex.log 2>&1
python3 sieve.py kite --nmax 10 --verify sample --sample 400 --dovetail "24:8" --shape-time 240 > logs/kite.log 2>&1
python3 regress.py kite myers > logs/regress.log 2>&1
