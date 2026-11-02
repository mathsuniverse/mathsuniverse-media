"""Forced-slope test on Modal for every near miss found by modal_explore.py.

    py -m modal run modal_slope.py --grid tetrakis
    py -m modal run modal_slope.py --grid kite --control      # hat + a periodic tile, to see the difference

For each chiral shape it measures, on discs of radius 5, 6, 7, the range of the minority-handedness share over ALL
coverings (slope.py). Hat: about 0.09 to 0.15 at R = 7-8, never near 1/2 (forced, -> 0.127). Periodic control: 0.21 to 0.49.
A near miss whose range stays narrow and away from 1/2 is a slope signal worth a closer look.
Results: results/slope/<grid>.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**", "candidates/**",
                                                  "__pycache__/**", "*.png"]))
app = modal.App("monotile-slope", image=image)


@app.function(cpu=1.0, memory=4096, timeout=3600, retries=1, max_containers=100)
def one(grid, rec, Rs):
    sys.path.insert(0, "/root/ms")
    import slope
    try:
        return rec, slope.run(grid, rec["cells"], Rs, budget=900)
    except Exception as e:  # noqa
        return rec, [dict(error=repr(e))]


HAT = [[0, 0, 0], [0, 0, 1], [0, 0, 2], [0, 0, 5], [0, 1, 4], [0, 1, 5], [1, 0, 2], [1, 0, 3]]
PER = [[0, 0, 0], [0, 0, 1], [0, 0, 2], [0, 0, 3], [0, 0, 4], [0, 0, 5], [0, 1, 2], [0, 1, 3], [0, 1, 4], [1, 0, 2], [1, 0, 3]]


@app.local_entrypoint()
def main(grid: str = "tetrakis", control: bool = False, rmax: int = 7):
    Rs = [float(r) for r in range(5, rmax + 1)]
    if control:
        recs = [dict(id="hat", cells=HAT, cls="OPEN"), dict(id="kite11_00059", cells=PER, cls="PERIODIC")]
    else:
        src = json.load(open(os.path.join(HERE, "results", "explore", f"{grid}.json")))
        recs, seen = [], set()
        for n, v in src.items():
            for r in v.get("near", []):
                key = json.dumps(sorted(map(tuple, r["cells"])))
                if key in seen:
                    continue
                seen.add(key); r = dict(r); r["n"] = int(n); recs.append(r)
    print(f"{len(recs)} shapes, radii {Rs}", flush=True)
    out = []
    for rec, res in one.starmap([(grid, r, Rs) for r in recs]):
        out.append(dict(id=rec.get("id"), n=rec.get("n"), cls=rec["cls"], tiles_per_domain=rec.get("tiles_per_domain"),
                        fail_R=rec.get("fail_R"), cells=rec["cells"], slope=res))
        last = [x for x in res if "minority_share_low" in x]
        if last:
            x = last[-1]
            print(f"  {rec.get('id') or rec.get('n')}: R={x['R']} minority share {x['minority_share_low']} .. {x['minority_share_high']}", flush=True)
    d = os.path.join(HERE, "results", "slope"); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{grid}{'_control' if control else ''}.json")
    json.dump(out, open(p, "w"), indent=1)
    print("Done. Results in", p)
