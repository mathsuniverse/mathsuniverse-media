"""Exact coincidence relations of a gluing rule (THEORY s14): keypoints of different copies that coincide in the
eigen-geometry beyond the chain glues give linear equations the tile's own quad must satisfy (in Z[z12]^4)."""
import numpy as np, itertools, sympy as sp
import fractile as F
from rules_k import blocks, RK
from spectre_exact import cx
def relations(steps, sq, refl, m=0, e=1, tol=1e-7):
    I=F.ifs(steps,sq,refl,m,e); q=I['quad']
    kids=[[F.ap(I['maps'][i],z) for z in q] for i in range(len(I['maps']))]
    B=blocks(steps)
    chain={(i,fr,i+1,to) for i,(a,fr,to) in enumerate(steps)}
    rows=[]; pairs=[]
    for (i,a),(j,b) in itertools.combinations([(i,a) for i in range(len(kids)) for a in range(4)],2):
        if i==j or abs(kids[i][a]-kids[j][b])>tol: continue
        if (i,a,j,b) in chain: continue
        pairs.append((i,a,j,b)); rows.append(B[i][a]-B[j][b])
    if not rows: return pairs, None
    A=sp.Matrix(np.vstack(rows))
    return pairs, A
def quad_vec(quad):  # stacked integer quad (4 points x 4 coords), q0 at origin
    return np.concatenate([np.array(p)-np.array(quad[0]) for p in quad])
if __name__=='__main__':
    import spectre_exact as SE
    sp_steps=[(60,3,1),(0,2,0),(60,3,1),(60,3,1),(0,2,0),(60,3,1),(-120,3,3)]
    pairs,A=relations(sp_steps,[(6,2),(5,1),(3,2),(0,1)],True,7,2)
    print("extra coincidences:",pairs)
    Q=quad_vec(SE.Tile('x').quad); print("Spectre quad satisfies them:", (np.array(A*sp.Matrix(Q))==0).all())
    K=A.nullspace(); print("kernel dimension (quads allowed, incl. translations):",len(K))
