"""The last 5 undecided 10-fold shapes (mirrors allowed): bigger patches, then read repeats off them. One container each.

    py -m modal run --detach modal_u5.py
Results (one file per shape, so parallel saves never overwrite each other):
    py -m modal volume get monotile-results u5 . --force
"""
import json, os, sys, time
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png", "*.pkl"]))
app = modal.App("monotile-u5", image=image)
vol = modal.Volume.from_name("monotile-results", create_if_missing=True)
SHAPES = [[0, 1, 2, 5, 4, 3, 6, 9, 8, 7], [0, 1, 3, 2, 4, 5, 8, 9, 7, 6], [0, 1, 3, 2, 4, 5, 7, 9, 8, 6],
          [0, 1, 3, 5, 6, 4, 7, 9, 8, 2], [0, 1, 3, 2, 5, 4, 8, 9, 6, 7]]


def _save(i, d):
    os.makedirs("/vol/u5", exist_ok=True)
    json.dump(d, open(f"/vol/u5/shape{i}.json", "w"), indent=1)
    vol.commit()


@app.function(cpu=1.0, memory=8192, timeout=5 * 3600, retries=0, max_containers=10, volumes={"/vol": vol})
def one(i):
    sys.path.insert(0, "/root/ms")
    import free2 as F2
    seq = SHAPES[i]
    S = F2.Search(seq, 10, True)
    t0 = time.time(); best = None; hist = []
    d = dict(seq=seq, status='running')
    for R in (2, 3, 4, 5, 6):
        try:
            r = S.cover(R * S.diam / 2, node_limit=4000000, time_limit=4500, scan=None)
        except Exception as e:
            r = None
        hist.append([R, r, S.nodes, round(time.time() - t0)])
        if r:
            best = (R, list(S.patch))
        d.update(hist=hist); _save(i, d)
        if not r:
            break
    if hist[-1][1] is False:
        d.update(status='done', cls='STUCK', fail_R=hist[-1][0])
    else:
        res, n = F2.patch_periods(S, max_tiles=80, top=600, patch=best[1], budget=3600, node_limit=50000) if best else (None, 0)
        if res:
            d.update(status='done', cls='PERIODIC', patch_R=best[0], **{k: list(v) if isinstance(v, tuple) else v for k, v in res.items()})
        else:
            d.update(status='done', cls='UNDECIDED' if res is None else 'NO REPEAT FOUND', patch_R=best[0] if best else None,
                     patch_tiles=len(best[1]) if best else 0, lattices_tested=n)
    d['seconds'] = round(time.time() - t0)
    _save(i, d)
    return d


@app.function(timeout=6 * 3600, volumes={"/vol": vol})
def orchestrate():
    for d in one.map(range(len(SHAPES)), order_outputs=False, return_exceptions=True):
        pass


@app.local_entrypoint()
def main():
    orchestrate.spawn()
    print("spawned 5 shapes. Results: py -m modal volume get monotile-results u5 . --force")
