"""Screen k-slot rules (rules_k{k}.json) for fractal tiles (THEORY s14)."""
import json, sys, math, time, itertools
import fractile as F
k=int(sys.argv[1]); rules=json.load(open(f'rules_k{k}.json'))
mu=(k+math.sqrt(k*k-4))/2; want=math.sqrt(mu)
t=time.time(); surv={}; nbad=0
for r in rules:
    steps=[tuple(s) for s in r['steps']]; sq=[tuple(x) for x in r['sq']]
    try:
        I=F.ifs(steps,sq,r['refl'],0,1)
    except Exception: nbad+=1; continue
    if I is None or abs(I['scale']-want)>1e-6: continue
    st=F.quad_stats(I)
    if not st['simple'] or st['sum_over_union']>1.15 or not (0.85<st['hull_cover']<1.15): continue
    key=tuple(sorted((round(a.real,6),round(a.imag,6),round(b.real,5),round(b.imag,5),f) for a,b,f in I['maps']))
    if key not in surv: surv[key]=dict(r, stats=st)
print(f"k={k}: {len(rules)} rules, {len(surv)} distinct pass the quad screen, {time.time()-t:.0f}s", flush=True)
out=[]
for r in surv.values():
    steps=[tuple(s) for s in r['steps']]; sq=[tuple(x) for x in r['sq']]
    for m,e in itertools.permutations(range(k),2):
        I=F.ifs(steps,sq,r['refl'],m,e)
        ov,cells,_=F.overlap(I,'X',depth=6 if k<7 else 5,grid=300)
        ovY,cellsY,_=F.overlap(I,'Y',depth=6 if k<7 else 5,grid=300)
        out.append(dict(r,m=m,e=e,ovX=ov,ovY=ovY,cellsX=cells,cellsY=cellsY))
        if ov<0.08 and ovY<0.08: print("PASS",r['steps'],r['sq'],r['refl'],"m",m,"e",e,"ovX %.3f ovY %.3f"%(ov,ovY),flush=True)
json.dump(out,open(f'screen_k{k}.json','w'))
print("done",len(out),time.time()-t)
