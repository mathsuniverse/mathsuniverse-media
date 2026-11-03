"""Re-test the outlines the free search left UNDECIDED (with mirrors), with a much larger budget, all in parallel.

    py -m modal run modal_free_retest.py                 # reads results_undecided12.txt (one outline per line)
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("silver-free-retest", image=image)


@app.function(cpu=1.0, memory=4096, timeout=3 * 3600, retries=1, max_containers=100)
def retest(seq):
    sys.path.insert(0, "/root/ms")
    import free2 as F2, time
    S = F2.Search(seq, 8, True); t = time.time(); res = None
    for R in (1.5, 2, 3, 4, 5):
        r = S.cover(R * S.diam / 2, node_limit=1000000, time_limit=1500)
        if r is None:
            res = dict(cls='UNDECIDED', at_R=R); break
        if not r:
            res = dict(cls='STUCK', fail_R=R); break
    if res is None:
        p = F2.periodic4(S, 16, 10, budget=2400)
        res = dict(cls='PERIODIC', **p[0]) if p[0] else dict(cls='OPEN', lattices=p[1], of=p[2])
    res['seconds'] = round(time.time() - t)
    return seq, res


@app.local_entrypoint()
def main(src: str = "results_undecided12.txt"):
    seqs = [json.loads(l) for l in open(os.path.join(HERE, src)) if l.strip()]
    print(f'{len(seqs)} outlines, with mirrors, large budget', flush=True)
    out = []
    for seq, res in retest.map(seqs, order_outputs=False):
        out.append(dict(seq=seq, result=res))
        print(f"  {res['cls']:10s} {seq}  {res}", flush=True)
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'results', 'free12_retest.json'), 'w'), indent=1)
    from collections import Counter
    print('Done:', dict(Counter(r['result']['cls'] for r in out)))
