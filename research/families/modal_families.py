"""Interpolating-family search on Modal (the hat's Tile(a,b) idea on the 45° grid, edges 1 and √2).

    py -m modal run modal_families.py                 # all families with 4..12 edges (about 4,000), 7 edge ratios each
    py -m modal run modal_families.py --mmax 14       # bigger (enumeration takes a few minutes locally first)

For each family it sieves Tile(1,0), Tile(0,1), Tile(1,1), Tile(1,2), Tile(2,1), Tile(2,3), Tile(3,2) on the 45° grid.
HAT-LIKE = both ends PERIODIC and some shape in between OPEN.  Any OPEN is printed.  Results: results/families.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "__pycache__/**", "*.png"]))
app = modal.App("families", image=image)
RATIOS = ((1, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 3), (3, 2))


@app.function(cpu=1.0, memory=4096, timeout=3000, retries=1, max_containers=100)
def test_chunk(chunk):
    sys.path.insert(0, "/root/ms")
    import families as Fm
    out = []
    for f in chunk:
        try: r = Fm.test_family(tuple(f), RATIOS)
        except Exception as e: r = {'error': repr(e)}
        out.append((f, {f'{a},{b}': v for (a, b), v in r.items()} if 'error' not in r else r))
    return out


@app.function(cpu=1.0, memory=4096, timeout=1800)
def enumerate_families(mmax):
    sys.path.insert(0, "/root/ms")
    import families as Fm
    return [list(f) for m in range(4, mmax + 1, 2) for f in Fm.families(m)]


@app.local_entrypoint()
def main(mmax: int = 12, per: int = 15):
    F = enumerate_families.remote(mmax)          # enumeration runs on Modal too, so nothing extra is needed on the PC
    chunks = [F[i:i + per] for i in range(0, len(F), per)]
    print(len(F), 'families in', len(chunks), 'jobs', flush=True)
    res, hits, hat = [], 0, 0
    path = os.path.join(HERE, "results", "families.json"); os.makedirs(os.path.dirname(path), exist_ok=True)
    for part in test_chunk.map(chunks, order_outputs=False):
        for f, r in part:
            res.append(dict(seq=f, result=r))
            vals = list(r.values())
            if 'OPEN' in vals:
                hits += 1
                ends = (r.get('1,0'), r.get('0,1'))
                tag = 'HAT-LIKE' if ends == ('PERIODIC', 'PERIODIC') else 'OPEN'
                hat += tag == 'HAT-LIKE'
                print(f"{tag}: family {f}  {r}", flush=True)
        json.dump(res, open(path, "w"))
        print(f"  progress {len(res)}/{len(F)}  OPEN families {hits}  hat-like {hat}", flush=True)
    print("Done. Results in", path)
