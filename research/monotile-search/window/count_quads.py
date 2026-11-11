"""Funnel over all quads for a rule: relations -> quad overlap -> corner-surviving words (no polygon tests)."""
import sys, json, time, itertools, numpy as np
import polysearch as PS, polysearch2 as P2
from relations import relations
from spectre_exact import cx
from shapely.geometry import Polygon
def funnel(steps,sq,refl,m,e,lens,qtol=1.05):
    pairs,A=relations(steps,sq,refl,m,e); A=None if A is None else np.array(A.tolist(),dtype=np.int64)
    R=[PS.reach(l) for l in lens]; out=[]; nq=0
    for e1 in R[0]:
      for e2 in R[1]:
        for e3 in R[2]:
          e4=PS.sub((0,0,0,0),PS.add(PS.add(e1,e2),e3))
          if e4 not in R[3]: continue
          Q=[(0,0,0,0),e1,PS.add(e1,e2),PS.add(PS.add(e1,e2),e3)]
          if A is not None and (A@np.concatenate(Q)).any(): continue
          qc=[cx(np.array(p)) for p in Q]; qa=Polygon([(z.real,z.imag) for z in qc])
          if not qa.is_valid or qa.area<=1e-9: continue
          nq+=1
          try: cl=P2.clusters(steps,sq,refl,m,e,qc)
          except Exception: continue
          ov=P2.quad_overlap(cl,qc)
          if ov>qtol: continue
          groups=P2.corner_groups(cl,qc)
          ccw=(sum((qc[i].conjugate()*qc[(i+1)%4]).imag for i in range(4))>0)
          arcs=[R[0][e1],R[1][e2],R[2][e3],R[3][e4]]; fl=[]
          for k in range(4):
              d={}
              for w in arcs[k]: d.setdefault((w[0],w[-1]),[]).append(w)
              fl.append(d)
          words=0
          for c in itertools.product(*[list(x.keys()) for x in fl]):
              sec=[];bad=False
              for k in range(4):
                  s,w=P2.sector(c[k][0],c[k-1][1],ccw)
                  if w==0: bad=True;break
                  sec.append((s,w))
              if bad: continue
              for g in groups:
                  acc=0
                  for (k,r,f) in g:
                      mk=P2.mask(*P2.place(*sec[k],r,f))
                      if acc&mk: bad=True;break
                      acc|=mk
                  if bad: break
              if bad: continue
              n=1
              for k in range(4): n*=len(fl[k][c[k]])
              words+=n
          if words: out.append(dict(quad=[list(q) for q in Q],overlap=ov,words=words))
    return nq,out
if __name__=='__main__':
    sp=[(60,3,1),(0,2,0),(60,3,1),(60,3,1),(0,2,0),(60,3,1),(-120,3,3)]; sq=[(6,2),(5,1),(3,2),(0,1)]
    t=time.time(); nq,out=funnel(sp,sq,True,7,2,(2,2,4,6))
    print("spectre rule: quads",nq,"surviving quads",len(out),"words",sum(o['words'] for o in out),round(time.time()-t),"s",flush=True)
    json.dump(out,open('polysearch2_quads_spectre.json','w'))
