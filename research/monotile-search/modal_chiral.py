"""The Spectre rule on Modal: every shape that tiles periodically with mirrors (all stored results on this PC: local sieves,
results/modal/*_shapes.json.gz, silver families) re-tested with mirror images forbidden.

    py -m modal run modal_chiral.py
Prints OPEN shapes (Spectre-type candidates: tile only aperiodically when mirrors are forbidden).
Results: results/chiral.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("monotile-chiral", image=image)


@app.function(cpu=1.0, memory=4096, timeout=3600, retries=1, max_containers=100)
def chunk(items):
    sys.path.insert(0, "/root/ms")
    import chiral
    return chiral.test_chunk(items)


@app.local_entrypoint()
def main(per: int = 40):
    import chiral
    from collections import Counter
    items = chiral.load_periodic()
    print(f'{len(items)} shapes that tile periodically with mirrors: {dict(Counter(g for g, _ in items))}', flush=True)
    out, c = [], Counter()
    for part in chunk.map([items[i:i + per] for i in range(0, len(items), per)], order_outputs=False):
        for r in part:
            out.append(r); c[r['cls']] += 1
            if r['cls'] == 'OPEN':
                print(f"   OPEN (no mirrors) {r['grid']} n={r['n']}: {r['cells']}", flush=True)
        if len(out) % 5000 < per:
            print(f'  {len(out)}/{len(items)}  {dict(c)}', flush=True)
    json.dump(out, open(os.path.join(HERE, 'results', 'chiral.json'), 'w'))
    print(f'Done: {dict(c)}  (STUCK = needs mirrors to tile at all; PERIODIC = repeats without mirrors too)')
