"""Settle the shapes the DFS left UNDECIDED, with the SAT patch builder (satpatch.py). Runs in the cloud, results in the volume.

    py -m modal run --detach modal_sat_retest.py
Progress:  py -m modal volume get monotile-results progress_sat.txt . --force
Results:   py -m modal volume get monotile-results sat_retest.json . --force
Control: the hat (12-fold, Tile(1, sqrt3)) is run first: with mirrors it must give big patches and no period, without mirrors STUCK.
"""
import json, os, sys, time
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png", "*.pkl"]))
app = modal.App("monotile-sat", image=image)
vol = modal.Volume.from_name("monotile-results", create_if_missing=True)
HAT = [7, 10, 0, 0, 2, 11, 1, 4, 6, 3, 5, 8, 6, 9]


def _lens(F, N, seq, spec):
    if spec is None:
        return None
    lam, swap = spec
    R = F.Ring(N); one = (1, 0, 0, 0); c = R.unit_sum([1, -1])
    L = {'r3': c, '2+r3': R.add((2, 0, 0, 0), c), 'phi': R.add(one, c), 'r2': c, '1+r2': R.add(one, c)}[lam]
    return [(L if (d % 2) != swap else one) for d in seq]


def _log(msg):
    p = "/vol/progress_sat.txt"
    with open(p, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")
    vol.commit()


@app.function(cpu=2.0, memory=24576, timeout=4 * 3600, retries=1, max_containers=40, volumes={"/vol": vol})
def one(item):
    sys.path.insert(0, "/root/ms")
    import free as F, satpatch as SP
    N, seq = item['N'], item['seq']
    lens = _lens(F, N, seq, item.get('lens'))
    res = {}
    for mir in ((True, False) if item.get('prev') in ('UNDECIDED/UNDECIDED', 'control') else (True,)):
        try:
            r = SP.classify_sat(seq, N, lens, mirror=mir, Rs=(2, 3, 4, 5, 6), time_limit=2400)
            r['hist'] = [[h[0], h[1], h[2]] for h in r['hist']]
        except Exception as e:
            r = dict(cls='error', error=repr(e)[:300])
        res['mirror' if mir else 'nomirror'] = r
    _log(f"N={N} {seq} lens={item.get('lens')} -> " +
         " ".join(f"{k}:{v['cls']}" + (f"(R{v.get('fail_R') or v.get('at_R')})" if v.get('fail_R') or v.get('at_R') else '')
                  + (f"[{v['tiles']} tiles]" if v.get('tiles') else '') for k, v in res.items()))
    return dict(item, result=res)


@app.function(timeout=8 * 3600, volumes={"/vol": vol})
def orchestrate(items):
    _log(f"sat retest: start, {len(items)} shapes (first = hat control)")
    out = []
    for r in one.map(items, order_outputs=False):
        out.append(r)
        json.dump(out, open("/vol/sat_retest.json", "w"), indent=1); vol.commit()
    from collections import Counter
    c = Counter(r['result'].get('mirror', {}).get('cls') for r in out)
    _log(f"sat retest: done {dict(c)}")


@app.local_entrypoint()
def main(src: str = "unresolved_sat.json"):
    items = [dict(N=12, seq=HAT, lens=['r3', False], prev='control')] + json.load(open(os.path.join(HERE, src)))
    orchestrate.spawn(items)
    print(f"spawned: {len(items)} shapes. Progress: py -m modal volume get monotile-results progress_sat.txt . --force")
