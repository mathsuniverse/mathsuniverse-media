"""Gluing rules with k slots whose double-step trace equals k (area-count condition, THEORY s13).
Copy i+1 is turned by a further `ang` and its quad vertex `to` is placed on vertex `fr` of copy i. The super-quad is
4 vertices of 4 copies (descending copy index, as in the Spectre). Optional final reflection R."""
import numpy as np, itertools, sys, json, time
from chainrules import ROT, Rref, E
def blocks(steps):
    rots=[ROT[0]]; Ls=[np.zeros((4,16),int)]; tot=0; seen={(0,ROT[0].tobytes(),Ls[0].tobytes())}
    for ang,fr,to in steps:
        tot=(tot+ang)%360; Rm=ROT[(tot//30)%12]
        L=rots[-1]@E[fr]+Ls[-1]-Rm@E[to]
        key=(Rm.tobytes(),L.tobytes())
        if key in {(a,b) for _,a,b in seen}: return None      # two copies in the same place
        seen.add((len(rots),Rm.tobytes(),L.tobytes())); Ls.append(L); rots.append(Rm)
    return [[rots[i]@E[v]+Ls[i] for v in range(4)] for i in range(len(rots))]
RK=np.kron(np.eye(4,dtype=int),Rref)
def run(k, angs, glue, vset=(0,1,2,3), out=None):
    t=time.time(); hits=[]; n=0
    for steps in itertools.product([(a,f,g) for a in angs for f,g in glue],repeat=k-1):
        B=blocks(steps)
        if B is None: continue
        mats=[]; meta=[]
        for idx in itertools.combinations(range(k-1,-1,-1),4):
            for vs in itertools.product(vset,repeat=4):
                S=np.vstack([B[i][v] for i,v in zip(idx,vs)])
                for refl in (True,False):
                    mats.append(RK@S if refl else S); meta.append((idx,vs,refl))
        M=np.array(mats,dtype=float); n+=len(M)
        M2=M@M
        # trace condition on the double step: char poly of M2 contains x^2 - k x + 1  <=>  mu=(k+sqrt(k^2-4))/2 is an eigenvalue
        mu=(k+np.sqrt(k*k-4))/2
        dets=np.linalg.det(M2-mu*np.eye(16))
        for j in np.nonzero(np.abs(dets)<1e-6*np.abs(np.linalg.det(M2-(mu+0.37)*np.eye(16)))+1e-9)[0]:
            idx,vs,refl=meta[j]; hits.append(dict(steps=[list(s) for s in steps],sq=[[int(i),int(v)] for i,v in zip(idx,vs)],refl=refl))
    print(f"k={k}: {n} rules, {len(hits)} with double-step trace {k}, {time.time()-t:.0f}s",flush=True)
    if out: json.dump(hits,open(out,'w'))
    return hits
if __name__=='__main__':
    # control: the Spectre rule must pass with k = 8
    sp=[(60,3,1),(0,2,0),(60,3,1),(60,3,1),(0,2,0),(60,3,1),(-120,3,3)]
    B=blocks(sp); S=np.vstack([B[i][v] for i,v in [(6,2),(5,1),(3,2),(0,1)]]); M2=((RK@S)@(RK@S)).astype(float)
    mu=4+np.sqrt(15); print("control Spectre: |det(M2-mu I)| =",abs(np.linalg.det(M2-mu*np.eye(16))))
    k=int(sys.argv[1])
    run(k,[0,60,-60,120,-120,180],[(3,1),(2,0),(3,3)],out=f'rules_k{k}.json')
