"""Fractal-tile test for Spectre-type gluing rules (THEORY s14).
A rule = chain steps (ang, fr, to), super-quad choice sq [(copy, vertex)], reflection flag; Mystic slot m (holds Y in
both supertiles) and empty slot e (missing in the Y-supertile). In the eigen-geometry the supertile is a similar copy
of the tile, so the rule is a 2-type graph-directed IFS of similarities. Valid rule <=> the pieces have disjoint
interiors (overlap only on a boundary of zero area) and positive area. Measured on a pixel grid."""
import numpy as np, cmath, math
Z=cmath.exp(1j*math.pi/6)
def chain(steps, quad):
    """transforms (a, b, f): z -> a*(conj z if f) + b, for copies 0..k-1 (before the reflection)"""
    trs=[(1+0j,0j,0)]; tot=0
    for ang,fr,to in steps:
        tot=(tot+ang)%360; r=Z**(tot//30)
        a,b,f=trs[-1]; p=a*(quad[fr].conjugate() if f else quad[fr])+b
        trs.append((r, p-r*quad[to], 0))
    return trs
def ap(t,z): a,b,f=t; return a*(z.conjugate() if f else z)+b
def comp(T,U):
    a,b,f=T; c,d,g=U
    if f: return (a*c.conjugate(), a*d.conjugate()+b, 1-g)
    return (a*c, a*d+b, g)
REF=(-1+0j,0j,1)    # z -> -conj z
def supermap(steps, sq, refl, quad):
    trs=chain(steps, quad)
    if refl: trs=[comp(REF,t) for t in trs]
    return trs, [ap(trs[i],quad[v]) for i,v in sq]
def eigen_quad(steps, sq, refl, iters=200):
    rng=np.random.default_rng(1); q=list(rng.normal(size=4)+1j*rng.normal(size=4))
    for _ in range(iters):
        _,q=supermap(steps,sq,refl,q); _,q=supermap(steps,sq,refl,q)
        q=[z-q[0] for z in q]; s=q[1]; q=[z/s for z in q]          # normalise: q0=0, q1=1
    return q
def similarity(P,Q):
    """similarity (a,b,f) with ap(t,P[j]) ~ Q[j]; returns it and the fit residual"""
    best=None
    for f in (0,1):
        p=[z.conjugate() if f else z for z in P]
        a=(Q[1]-Q[0])/(p[1]-p[0]); b=Q[0]-a*p[0]
        res=max(abs(a*x+b-y) for x,y in zip(p,Q))/abs(a)
        if best is None or res<best[1]: best=((a,b,f),res)
    return best
def inv(t):
    a,b,f=t
    if f: return (1/a.conjugate(), -(b/a).conjugate(), 1)
    return (1/a, -b/a, 0)
def ifs(steps, sq, refl, m, e):
    q=eigen_quad(steps,sq,refl)
    trs,Q1=supermap(steps,sq,refl,q)
    S,res=similarity(q,Q1)
    if res>1e-6 or abs(S[0])<=1+1e-9: return None
    Si=inv(S); maps=[comp(Si,t) for t in trs]
    X=[(i,('Y' if i==m else 'X')) for i in range(len(maps))]
    Y=[(i,('Y' if i==m else 'X')) for i in range(len(maps)) if i!=e]
    return dict(quad=q, maps=maps, X=X, Y=Y, scale=abs(S[0]))
def points(I, typ, depth):
    """attractor points of type typ, labelled by top-level piece"""
    pts={'X':np.array([sum(I['quad'])/4]), 'Y':np.array([sum(I['quad'])/4])}
    for _ in range(depth):
        new={}
        for T in ('X','Y'):
            arr=[]
            for i,c in I[T]:
                a,b,f=I['maps'][i]; z=pts[c]; arr.append(a*(np.conj(z) if f else z)+b)
            new[T]=np.concatenate(arr)
        pts=new
    # labels: rebuild one level on top
    out=[]; lab=[]
    for j,(i,c) in enumerate(I[typ]):
        a,b,f=I['maps'][i]; z=pts[c]; out.append(a*(np.conj(z) if f else z)+b); lab.append(np.full(len(z),j))
    return np.concatenate(out), np.concatenate(lab)
def overlap(I, typ='X', depth=6, grid=400):
    z,lab=points(I,typ,depth)
    x,y=z.real,z.imag; span=max(np.ptp(x),np.ptp(y))
    ix=((x-x.min())/span*(grid-1)).astype(int); iy=((y-y.min())/span*(grid-1)).astype(int)
    cell=ix*grid+iy
    owners={}
    import collections
    cnt=collections.defaultdict(set)
    for c,l in zip(cell.tolist(),lab.tolist()): cnt[c].add(l)
    multi=sum(1 for s in cnt.values() if len(s)>1)
    return multi/len(cnt), len(cnt), len(z)
if __name__=='__main__':
    sp=[(60,3,1),(0,2,0),(60,3,1),(60,3,1),(0,2,0),(60,3,1),(-120,3,3)]
    I=ifs(sp,[(6,2),(5,1),(3,2),(0,1)],True,7,2)
    print("Spectre: scale",I['scale'],"(expect sqrt(4+sqrt15) =",math.sqrt(4+math.sqrt(15)),")")
    for d in (4,5,6): print(" depth",d,"overlap fraction, cells, points:",overlap(I,'X',d))

from shapely.geometry import Polygon
from shapely.ops import unary_union
def quad_stats(I, typ='X'):
    q=I['quad']; P=Polygon([(z.real,z.imag) for z in q])
    kids=[]
    for i,c in I[typ]:
        w=[ap(I['maps'][i],z) for z in q]; kids.append(Polygon([(z.real,z.imag) for z in w]))
    tot=sum(k.area for k in kids); uni=unary_union([k.buffer(0) for k in kids]).area
    return dict(simple=P.is_valid, quad_area=P.area, sum_over_union=tot/uni if uni else 99, hull_cover=uni/P.area)
