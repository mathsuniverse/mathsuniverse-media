"""Find polygons that realise a gluing rule (THEORY s14). Arcs between consecutive keypoints are equal-edge
12-direction paths; the quad must satisfy the rule's coincidence relations; the Mystic's second tile is found by
edge matching. Every survivor passes realise.valid at levels 1..3."""
import numpy as np, itertools, math, cmath, time, sys, json
from shapely.geometry import Polygon
import fractile as F, realise as RL
from relations import relations, quad_vec
from spectre_exact import ROT, cx, MC
import sympy as sp
U=[tuple(int(x) for x in ROT[d]@np.array([1,0,0,0])) for d in range(12)]
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def reach(L):
    """vectors reachable in exactly L unit steps -> list of direction words (no immediate reversal)"""
    words={(0,0,0,0):[()]}
    for _ in range(L):
        new={}
        for v,ws in words.items():
            for w in ws:
                for d in range(12):
                    if w and (d-w[-1])%12==6: continue
                    new.setdefault(add(v,U[d]),[]).append(w+(d,))
        words=new
    return words
def turns_ok(word_cycle, max_turn=5):
    n=len(word_cycle)
    for i in range(n):
        t=(word_cycle[(i+1)%n]-word_cycle[i])%12
        if t==6: return False
        if min(t,12-t)>max_turn: return False
    return True
def search(steps, sq, refl, m, e, lens, max_g=None, L=3, verbose=True, limit_time=3600):
    t0=time.time()
    pairs,A=relations(steps,sq,refl,m,e)
    Anp=None if A is None else np.array(A.tolist(),dtype=np.int64)
    R=[reach(l) for l in lens]
    found=[]; nq=0; npoly=0
    for e1 in R[0]:
        for e2 in R[1]:
            for e3 in R[2]:
                e4=sub((0,0,0,0),add(add(e1,e2),e3))
                if e4 not in R[3]: continue
                Q=[(0,0,0,0),e1,add(e1,e2),add(add(e1,e2),e3)]
                if Anp is not None and (Anp@np.concatenate(Q)).any(): continue
                qc=[cx(np.array(p)) for p in Q]
                if Polygon([(z.real,z.imag) for z in qc]).area<=1e-9: continue
                nq+=1
                for w in itertools.product(R[0][e1],R[1][e2],R[2][e3],R[3][e4]):
                    word=sum(w,())
                    if not turns_ok(word): continue
                    # polygon vertices
                    pts=[(0,0,0,0)]
                    for d in word[:-1]: pts.append(add(pts[-1],U[d]))
                    poly=[cx(np.array(p)) for p in pts]
                    pg=Polygon([(z.real,z.imag) for z in poly])
                    if not pg.is_valid or pg.area<=0: continue
                    npoly+=1
                    # level-1 X cluster with a single tile in the Mystic slot (its second tile left as a hole)
                    obj=RL.level(steps,sq,refl,m,e,qc,poly,(1+0j,0j,0),1)
                    if RL.overlaps(obj['X'][0][:len(steps)+1] if False else _single(obj,steps,sq,refl,m,e,qc),poly): continue
                    # Mystic second tile: placements sharing a full edge with P (reversed), 12 rotations, no flip
                    for g in mystic_candidates(poly):
                        ok,lev,T=RL.valid(steps,sq,refl,m,e,qc,poly,g,L)
                        if ok:
                            found.append(dict(word=list(word),quad_idx=[0,len(w[0]),len(w[0])+len(w[1]),len(w[0])+len(w[1])+len(w[2])],g=[g[0].real,g[0].imag,g[1].real,g[1].imag,g[2]]))
                            if verbose: print("FOUND",word,flush=True)
                    if time.time()-t0>limit_time: return found,nq,npoly,'time'
    return found,nq,npoly,'done'
def _single(obj,steps,sq,refl,m,e,qc):
    trs,_=F.supermap(steps,sq,refl,qc); return trs
def mystic_candidates(poly):
    n=len(poly); out=[]
    P=Polygon([(z.real,z.imag) for z in poly])
    for r in range(12):
        rz=cmath.exp(1j*math.pi*r/6)
        for i in range(n):
            for j in range(n):
                # map edge j of rotated copy onto edge i of P reversed: rz*poly[j+1] -> poly[i], rz*poly[j] -> poly[i+1]
                a0,a1=poly[i],poly[(i+1)%n]; b0,b1=rz*poly[j],rz*poly[(j+1)%n]
                if abs((b1-b0)+(a1-a0))>1e-9: continue
                tvec=a0-b1; g=(rz,tvec,0)
                Q=Polygon([((F.ap(g,z)).real,(F.ap(g,z)).imag) for z in poly])
                if Q.is_valid and P.intersection(Q).area<1e-6: out.append(g)
    # dedupe
    seen=set(); res=[]
    for g in out:
        k=(round(g[0].real,6),round(g[0].imag,6),round(g[1].real,6),round(g[1].imag,6))
        if k not in seen: seen.add(k); res.append(g)
    return res
if __name__=='__main__':
    sp_steps=[(60,3,1),(0,2,0),(60,3,1),(60,3,1),(0,2,0),(60,3,1),(-120,3,3)]
    t=time.time()
    f,nq,npoly,st=search(sp_steps,[(6,2),(5,1),(3,2),(0,1)],True,7,2,(2,2,4,6),limit_time=5400)
    print("control: quads",nq,"polygons",npoly,"found",len(f),st,round(time.time()-t),"s")
    json.dump(f,open('polysearch_spectre_control.json','w'))
