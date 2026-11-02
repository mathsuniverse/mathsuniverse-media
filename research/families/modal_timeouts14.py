"""Re-test the families that timed out in the 14-edge screen, with a much longer time cap (10 min each).

    py -m modal run modal_timeouts14.py
Reads results/families14_screen.json, writes results/families14_timeouts.json.
Prints a line for every family whose ends pass, and CANDIDATE for any in-between shape still OPEN.
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "__pycache__/**", "*.png"]))
app = modal.App("timeouts14", image=image)


def _one(f, q):
    sys.path.insert(0, "/root/ms")
    import families as Fm
    try:
        r = Fm.test_family_hat(tuple(f), tcap=8, rcap=6)
        q.put({(k if isinstance(k, str) else f'{k[0]},{k[1]}'): v for k, v in r.items()})
    except Exception as e:
        q.put({'error': repr(e)})


@app.function(cpu=1.0, memory=8192, timeout=900, retries=1, max_containers=100)
def check(f, limit=600):
    import multiprocessing as mp, queue
    q = mp.Queue(); p = mp.Process(target=_one, args=(f, q)); p.start()
    try:
        r = q.get(timeout=limit); p.join(5)
    except queue.Empty:
        p.kill(); p.join(); r = {'timeout': f'over {limit}s'}
    return dict(seq=f, result=r)


@app.local_entrypoint()
def main():
    src = json.load(open(os.path.join(HERE, "results", "families14_screen.json")))
    todo = [x['seq'] for x in src if 'timeout' in x['result']]
    print(f'{len(todo)} timed-out families to re-test (10 min each, up to 100 at once)', flush=True)
    out, path = [], os.path.join(HERE, "results", "families14_timeouts.json")
    n_ends = n_to = 0
    for r in check.map(todo, order_outputs=False):
        out.append(r); res = r['result']
        if 'timeout' in res: n_to += 1
        if '1,0' in res:
            n_ends += 1
            inner = {k: v for k, v in res.items() if k not in ('1,0', '0,1')}
            tag = 'CANDIDATE' if 'OPEN' in inner.values() else 'ends ok'
            print(f'{tag:10s} {r["seq"]}  {inner}', flush=True)
        if len(out) % 100 == 0:
            print(f'  {len(out)}/{len(todo)}  ends ok {n_ends}  still timing out {n_to}', flush=True)
            json.dump(out, open(path, "w"))
    json.dump(out, open(path, "w"))
    print(f'Done: {len(out)} re-tested, ends ok {n_ends}, still timing out {n_to}.')
