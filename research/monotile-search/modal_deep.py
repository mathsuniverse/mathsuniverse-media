"""Deep test of free-search candidates on Modal (one worker per outline):
patches out to radius 6, repeat search with vectors up to 12 edges and up to 16 tiles per repeat (all patterns),
with mirrors and without mirrors, plus the mirror ratio of the largest patch.

    py -m modal run modal_deep.py --src candidates14_openopen.json
    py -m modal run modal_deep.py --src results/free14.json --pick OPEN/STUCK      # every OPEN/STUCK of the 14-edge run
Results: results/deep_<name>.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("silver-deep", image=image)


@app.function(cpu=1.0, memory=8192, timeout=6 * 3600, retries=1, max_containers=100)
def deep(seq, mirror):
    sys.path.insert(0, "/root/ms")
    import free2 as F2, time
    S = F2.Search(seq, 8, mirror); t = time.time(); res = dict(mirror=mirror)
    for R in (2, 3, 4, 5, 6):
        r = S.cover(R * S.diam / 2, node_limit=3000000, time_limit=3600)
        if r is None:
            res.update(cls='UNDECIDED', at_R=R); break
        if not r:
            res.update(cls='STUCK', fail_R=R); break
        res['covered_R'] = R
        a = sum(1 for oi, _ in S.patch if S.orients[oi][1] == 0); b = len(S.patch) - a
        res['patch'] = dict(tiles=len(S.patch), normal=a, mirrored=b)
    if 'cls' not in res:
        p = F2.periodic4(S, 16, 12, budget=4 * 3600)
        if p[0]:
            res.update(cls='PERIODIC', **p[0])
        else:
            res.update(cls='OPEN', lattices_tested=p[1], of=p[2], undecided=p[3], complete=p[0] is False)
    res['seconds'] = round(time.time() - t)
    return seq, res


@app.local_entrypoint()
def main(src: str = "candidates14_openopen.json", pick: str = ""):
    data = json.load(open(os.path.join(HERE, src)))
    if pick:
        a, b = pick.split('/')
        seqs = [r['seq'] for r in data if 'mirror' in r['result'] and r['result']['mirror']['cls'] == a
                and r['result']['nomirror']['cls'] == b]
    else:
        seqs = data
    jobs = [(s, m) for s in seqs for m in ((True, False) if not pick or pick.split('/')[1] != 'STUCK' else (True,))]
    print(f'{len(seqs)} outlines, {len(jobs)} deep tests', flush=True)
    out = []
    for seq, res in deep.starmap(jobs, order_outputs=False):
        out.append(dict(seq=seq, result=res))
        print(f"  {res['cls']:9s} {'mirrors' if res['mirror'] else 'no mirrors':10s} {seq}  {res}", flush=True)
    name = os.path.splitext(os.path.basename(src))[0] + (('_' + pick.replace('/', '-')) if pick else '')
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'results', f'deep_{name}.json'), 'w'), indent=1)
    from collections import Counter
    print('Done:', dict(Counter((r['result']['cls'], r['result']['mirror']) for r in out)))
