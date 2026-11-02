"""Silver inverse cut-and-project on Modal: sweep edge stars with rational density and two label schemes.

    py -m modal run modal_silver.py                 # all stars below, labels = tile type and tile type + neighbours
    py -m modal run modal_silver.py --schemes type --minutes 10   # fast pass, each job capped at 10 minutes (max 13)

For each star (a,b,c,d) with 2ac + 4bd = (a+c)(b+d) (so one tile copy per silver tile has a whole-number area), the solver
looks for ONE shape S and one orientation per label that covers the deformed Ammann–Beenker patch exactly.
Any solution prints as FOUND with its size and whether it is connected. Results: results/silver_inverse.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "numpy", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "__pycache__/**", "*.png"]))
app = modal.App("silver-inverse", image=image)

STARS = [(1, 1, 4, 3), (1, 1, 5, 2), (1, 2, 5, 1), (1, 2, 6, 2), (1, 3, 4, 1), (2, 1, 3, 7), (2, 1, 4, 5), (2, 1, 6, 4),
         (2, 4, 6, 1), (2, 5, 4, 1), (3, 1, 2, 7), (3, 1, 3, 6), (3, 6, 3, 1), (4, 1, 1, 3), (4, 1, 2, 5), (4, 1, 4, 6),
         (4, 3, 1, 1), (4, 5, 2, 1)]


@app.function(cpu=1.0, memory=8192, timeout=1500, retries=0, max_containers=40)
def run(star, scheme, r, rz, limit_s):
    sys.path.insert(0, "/root/ms")
    import silver as S, silver_run as SR, engine as E_
    B = S.star(*star)
    if not S.valid(B):
        return dict(star=star, scheme=scheme, note="not a valid shape change")
    V, T, polys = S.build(rz + 6, B)
    lab = None if scheme == "type" else SR.nbr_labels(T, 1)
    sols, msg = S.solve(T, polys, B, r=r, Rz=rz, labels=lab, limit=10, time_limit=limit_s)
    return dict(star=star, scheme=scheme, msg=msg,
                solutions=[dict(size=len(s), connected=E_.is_connected(S.g, s), cells=[list(c) for c in s],
                                orient={str(k): v for k, v in o.items()}) for s, o in sols])


@app.local_entrypoint()
def main(r: float = 5.0, rz: float = 11.0, schemes: str = "type,type+neighbours", minutes: int = 12):
    minutes = min(minutes, 13)      # a solve longer than ~15 min starves Modal's 900 s heartbeat and the job is killed
    jobs = [(st, sc, r, rz, minutes * 60) for st in STARS for sc in schemes.split(",")]
    out = []
    path = os.path.join(HERE, "results", "silver_inverse.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for res in run.starmap(jobs, order_outputs=False):
        out.append(res)
        n = len(res.get("solutions", []))
        tag = "FOUND" if n else "none"
        con = sum(1 for s in res.get("solutions", []) if s["connected"])
        print(f"{tag:5s} star {res['star']} labels={res['scheme']}: {n} solutions ({con} connected)  {res.get('msg', res.get('note'))}", flush=True)
        json.dump(out, open(path, "w"), indent=1)          # saved after every job
    print("Done. Results in results/silver_inverse.json")
