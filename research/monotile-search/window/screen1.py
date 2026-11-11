"""Stage 1 screen: eigen-quad simple, child quads tile the parent like the Spectre's, one rule per distinct geometry."""
import json, sys, math, time
from multiprocessing import Pool
import fractile as F
k=int(sys.argv[1]); mu=(k+math.sqrt(k*k-4))/2; want=math.sqrt(mu)
def one(r):
    steps=[tuple(s) for s in r['steps']]; sq=[tuple(x) for x in r['sq']]
    try: I=F.ifs(steps,sq,r['refl'],0,1)
    except Exception: return None
    if I is None or abs(I['scale']-want)>1e-6: return None
    st=F.quad_stats(I)
    if not st['simple'] or st['sum_over_union']>1.10 or not (0.9<st['hull_cover']<1.1): return None
    key=tuple(sorted((round(a.real,5),round(a.imag,5),round(b.real,4),round(b.imag,4),f) for a,b,f in I['maps']))
    return key, dict(r, stats=st)
if __name__=='__main__':
    rules=json.load(open(f'rules_k{k}.json')); t=time.time(); surv={}; n=0
    with Pool(2) as p:
        for res in p.imap_unordered(one, rules, chunksize=2000):
            n+=1
            if res and res[0] not in surv: surv[res[0]]=res[1]
            if n%200000==0: print(n, len(surv), round(time.time()-t), flush=True)
    json.dump(list(surv.values()), open(f'screen1_k{k}.json','w'))
    print(f"k={k}: {len(rules)} rules -> {len(surv)} distinct geometries pass, {time.time()-t:.0f}s", flush=True)
