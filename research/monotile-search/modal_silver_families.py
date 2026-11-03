"""Complete (not sampled) search of hat-style families on the silver kite grid.

    py -m modal run modal_silver_families.py --m 12
    py -m modal run modal_silver_families.py --m 14
Stage 1: all outline families with m edges (49 slices). Stage 2: every family x every edge-length pair (A, B) from the silver
kite's sides x every start vertex -> every balanced grid shape (exact). Stage 3: every distinct shape sieved with certificates
(tori <= 12, discs R <= 6, then OPEN survivors at 24 / R 8). Prints OPEN shapes. Results: results/silver_families<m>.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("silver-families", image=image)
TURNS = (0, 1, 2, 3, -1, -2, -3)


@app.function(cpu=1.0, memory=8192, timeout=7200, retries=1, max_containers=49)
def enum_slice(m, t1, t2):
    sys.path.insert(0, "/root/ms")
    import families as Fm
    return [list(f) for f in Fm.families(m, True, first=(t1, t2), max_straight=1)]


@app.function(cpu=1.0, memory=4096, timeout=3600, retries=1, max_containers=100)
def realise(chunk):
    sys.path.insert(0, "/root/ms")
    import silver_families as S
    ctx = S.Ctx()
    out = {}
    for f in chunk:
        for sh, lab in S.family_shapes(ctx, tuple(f)).items():
            out.setdefault(sh, (f, lab))
    return [(list(map(list, sh)), f, lab) for sh, (f, lab) in out.items()]


@app.function(cpu=1.0, memory=4096, timeout=3600, retries=1, max_containers=100)
def sieve(items):
    sys.path.insert(0, "/root/ms")
    import engine as E, grids as G
    g = G.get('silverkite')
    res = []
    for cells, f, lab in items:
        cs = [tuple(c) for c in cells]
        r = E.classify(g, cs, tcap=12, rcap=6, time_limit=300)
        if r['cls'] == 'OPEN':
            r = E.classify(g, cs, tcap=24, rcap=8, tmin=r.get('tori_complete_upto') or 12, rmin=6, time_limit=900)
        res.append(dict(cells=cells, family=f, lengths=lab, n=len(cells), cls=r['cls'],
                        fail_R=r.get('fail_R'), tiles=r.get('tiles_per_domain')))
    return res


@app.local_entrypoint()
def main(m: int = 12, per: int = 40):
    seen, F = set(), []
    for part in enum_slice.starmap([(m, a, b) for a in TURNS for b in TURNS], order_outputs=False):
        for f in part:
            t = tuple(f)
            if t not in seen:
                seen.add(t); F.append(f)
    print(f'{len(F)} outline families with {m} edges', flush=True)
    shapes = {}
    for part in realise.map([F[i:i + per] for i in range(0, len(F), per)], order_outputs=False):
        for sh, f, lab in part:
            shapes.setdefault(tuple(map(tuple, sh)), (f, lab))
    items = [(list(map(list, sh)), f, lab) for sh, (f, lab) in shapes.items()]
    from collections import Counter
    print(f'{len(items)} distinct balanced silver-kite shapes realised; sizes {sorted(Counter(len(i[0]) for i in items).items())}',
          flush=True)
    out, counts = [], Counter()
    for part in sieve.map([items[i:i + 20] for i in range(0, len(items), 20)], order_outputs=False):
        for r in part:
            out.append(r); counts[r['cls']] += 1
            if r['cls'] == 'OPEN':
                print(f"   OPEN n={r['n']} family {r['family']} lengths {r['lengths']}: {r['cells']}", flush=True)
        if len(out) % 2000 < 20:
            print(f'  sieved {len(out)}/{len(items)}  {dict(counts)}', flush=True)
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'results', f'silver_families{m}.json'), 'w'))
    print(f'Done: {dict(counts)}')
