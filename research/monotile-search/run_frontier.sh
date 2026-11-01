#!/bin/bash
# Frontier grids, in priority order (tetrakis deepest).  Usage: ./run_frontier.sh [TETRAKIS_NMAX]
cd "$(dirname "$0")"
NT=${1:-12}
set -x
python3 sieve.py tetrakis --nmax $NT --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/tetrakis.log 2>&1
python3 sieve.py drafter --nmax 11 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/drafter.log 2>&1
python3 sieve.py floret --nmax 7 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/floret.log 2>&1
python3 sieve.py triakis --nmax 11 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/triakis.log 2>&1
python3 sieve.py rhomb --nmax 9 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/rhomb.log 2>&1
python3 sieve.py cairo --nmax 7 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/cairo.log 2>&1
python3 sieve.py prismatic --nmax 7 --verify sample --sample 400 --dovetail "24:8,48:12" --shape-time 90 > logs/prismatic.log 2>&1
