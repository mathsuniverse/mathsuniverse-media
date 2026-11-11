"""Polygon realisation of gluing rules, in the cloud (window/polysearch2.py, THEORY s14).

Start (returns at once):
    py -m modal run --detach modal_poly.py --rule spectre
Progress (any time):
    py -m modal volume get monotile-results progress_poly.txt . --force
Result: /vol/poly_<rule>.json (every polygon + Mystic placement that passes levels 1-3)

rule spectre = the Spectre's own rule with arcs (2,2,4,6): control. It must find the Spectre, and tells us whether the
Spectre is the only polygon that realises its rule. rule file:<name> = rules listed in window/<name>.json.
"""
import json, os, sys, time
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("numpy", "shapely", "sympy")
         .add_local_dir(os.path.join(HERE, "window"), "/root/win",
                        ignore=["rules_k*.json", "*.log", "screen*_k*.json", "polysearch*.json", "__pycache__/**", "*.png"]))
app = modal.App("monotile-poly", image=image)
vol = modal.Volume.from_name("monotile-results", create_if_missing=True)

SPECTRE = dict(name='spectre', steps=[(60, 3, 1), (0, 2, 0), (60, 3, 1), (60, 3, 1), (0, 2, 0), (60, 3, 1), (-120, 3, 3)],
               sq=[(6, 2), (5, 1), (3, 2), (0, 1)], refl=True, m=7, e=2, lens=(2, 2, 4, 6))


def _setup():
    sys.path.insert(0, '/root/win'); os.chdir('/root/win')
    import warnings; warnings.filterwarnings('ignore')


def _rules(rule):
    if rule == 'spectre': return [SPECTRE]
    if rule.startswith('file:'):
        _setup()
        return json.load(open('/root/win/%s.json' % rule[5:]))
    raise ValueError(rule)


@app.function(cpu=1.0, memory=4096, timeout=6 * 3600, retries=2, max_containers=100)
def funnel_part(R, i):
    """quads whose first side is the i-th vector of reach(lens[0]), with their corner-surviving word counts"""
    _setup()
    import numpy as np, itertools
    import polysearch as PS, polysearch2 as P2
    from relations import relations
    from spectre_exact import cx
    from shapely.geometry import Polygon
    steps, sq, refl, m, e, lens = [R[k] for k in ('steps', 'sq', 'refl', 'm', 'e', 'lens')]
    steps = [tuple(s) for s in steps]; sq = [tuple(s) for s in sq]
    pairs, A = relations(steps, sq, refl, m, e); A = None if A is None else np.array(A.tolist(), dtype=np.int64)
    RR = [PS.reach(l) for l in lens]
    e1 = sorted(RR[0])[i]; out = []
    for e2 in RR[1]:
        for e3 in RR[2]:
            e4 = PS.sub((0, 0, 0, 0), PS.add(PS.add(e1, e2), e3))
            if e4 not in RR[3]: continue
            Q = [(0, 0, 0, 0), e1, PS.add(e1, e2), PS.add(PS.add(e1, e2), e3)]
            if A is not None and (A @ np.concatenate(Q)).any(): continue
            qc = [cx(np.array(p)) for p in Q]; qa = Polygon([(z.real, z.imag) for z in qc])
            if not qa.is_valid or qa.area <= 1e-9: continue
            try: cl = P2.clusters(steps, sq, refl, m, e, qc)
            except Exception: continue
            ov = P2.quad_overlap(cl, qc)
            if ov > 1.05: continue
            groups = P2.corner_groups(cl, qc)
            ccw = (sum((qc[k].conjugate() * qc[(k + 1) % 4]).imag for k in range(4)) > 0)
            arcs = [RR[0][e1], RR[1][e2], RR[2][e3], RR[3][e4]]; fl = []
            for k in range(4):
                d = {}
                for w in arcs[k]: d.setdefault((w[0], w[-1]), []).append(w)
                fl.append(d)
            words = 0
            for c in itertools.product(*[list(x.keys()) for x in fl]):
                sec = []; bad = False
                for k in range(4):
                    s, w = P2.sector(c[k][0], c[k - 1][1], ccw)
                    if w == 0: bad = True; break
                    sec.append((s, w))
                if bad: continue
                for g in groups:
                    acc = 0
                    for (k, r, f) in g:
                        mk = P2.mask(*P2.place(*sec[k], r, f))
                        if acc & mk: bad = True; break
                        acc |= mk
                    if bad: break
                if bad: continue
                n = 1
                for k in range(4): n *= len(fl[k][c[k]])
                words += n
            if words: out.append(dict(quad=[list(q) for q in Q], overlap=ov, words=words))
    return R['name'], out


@app.function(cpu=1.0, memory=4096, timeout=6 * 3600, retries=2, max_containers=200)
def poly_chunk(R, quads):
    _setup()
    import polysearch2 as P2
    steps = [tuple(s) for s in R['steps']]; sq = [tuple(s) for s in R['sq']]
    f, st, s = P2.search(steps, sq, R['refl'], R['m'], R['e'], tuple(R['lens']), qtol=1.05, limit_time=5.5 * 3600,
                         verbose=False, only_quads=quads)
    return R['name'], len(quads), f, st, s


def _log(msg):
    with open('/vol/progress_poly.txt', 'a') as fh:
        fh.write(time.strftime('%Y-%m-%d %H:%M:%S ') + msg + '\n')
    vol.commit()


@app.function(timeout=24 * 3600, volumes={"/vol": vol}, retries=0, memory=8192, cpu=1.0)
def orchestrate(rule, chunk_words=60000):
    rules = _rules(rule)
    for R in rules:
        _setup(); import polysearch as PS
        n1 = len(PS.reach(R['lens'][0]))
        _log(f"rule {R['name']}: funnel over {n1} first sides")
        quads = []
        for name, part in funnel_part.starmap([(R, i) for i in range(n1)], order_outputs=False):
            quads += part
        tot = sum(q['words'] for q in quads)
        _log(f"rule {R['name']}: {len(quads)} quads survive, {tot} words")
        quads.sort(key=lambda q: q['overlap'])
        chunks, cur, cw = [], [], 0
        for q in quads:
            cur.append(q['quad']); cw += q['words']
            if cw >= chunk_words: chunks.append(cur); cur, cw = [], 0
        if cur: chunks.append(cur)
        found, done, agg = [], 0, {}
        for name, nq, f, st, s in poly_chunk.starmap([(R, c) for c in chunks], order_outputs=False):
            done += 1; found += f
            for k, v in st.items(): agg[k] = agg.get(k, 0) + v
            if f or done % 25 == 0 or done == len(chunks):
                _log(f"rule {name}: {done}/{len(chunks)} chunks, found {len(found)} " +
                     ' '.join(str(x['word']) for x in found[-3:]) + (' TIMEOUT' if s == 'time' else ''))
                with open(f"/vol/poly_{R['name']}.json", 'w') as fh: json.dump(dict(found=found, stats=agg), fh)
                vol.commit()
        _log(f"rule {R['name']}: DONE, found {len(found)}, stats {agg}")


@app.local_entrypoint()
def main(rule: str = "spectre"):
    orchestrate.spawn(rule)
    print("Started rule", rule)
    print("Progress: py -m modal volume get monotile-results progress_poly.txt . --force")
