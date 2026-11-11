"""Realise a gluing rule by a polygon (THEORY s14): tile P with 4 marked keypoints (its quad), Mystic Y = P + g(P),
X-supertile = k copies (slot m holds a Y), Y-supertile = same without slot e. Test levels 1..L with real polygons."""
import numpy as np, math, cmath, itertools
from shapely.geometry import Polygon
from shapely.strtree import STRtree
import fractile as F
from spectre_exact import ROT, cx
Z=cmath.exp(1j*math.pi/6)
U=[ROT[d]@np.array([1,0,0,0]) for d in range(12)]
def level(steps, sq, refl, m, e, quad, poly, g, L):
    """returns list of tile transforms of the level-L X-supertile and its quad"""
    obj={'X':([(1+0j,0j,0)],list(quad)), 'Y':([(1+0j,0j,0),g],list(quad))}
    for _ in range(L):
        trs,Q1=F.supermap(steps,sq,refl,obj['X'][1])
        new={}
        for T in ('X','Y'):
            tiles=[]
            for i,t in enumerate(trs):
                if T=='Y' and i==e: continue
                c='Y' if i==m else 'X'
                tiles+= [F.comp(t,u) for u in obj[c][0]]
            new[T]=(tiles,Q1)
        obj=new
    return obj
def overlaps(tiles, poly, tol=1e-6):
    P=[Polygon([(z.real,z.imag) for z in (F.ap(t,w) for w in poly)]) for t in tiles]
    if not all(p.is_valid for p in P): return True
    tree=STRtree(P)
    for i,p in enumerate(P):
        for j in tree.query(p):
            if j>i and p.intersection(P[j]).area>tol: return True
    return False
def solid(tiles, poly):
    """the cluster is one piece with no holes (a supertile must be a solid region)"""
    from shapely.ops import unary_union
    P=[Polygon([(z.real,z.imag) for z in (F.ap(t,w) for w in poly)]) for t in tiles]
    u=unary_union([p.buffer(1e-7) for p in P]).buffer(-1e-7)
    if u.geom_type!='Polygon': return False
    return len(u.interiors)==0
def valid(steps, sq, refl, m, e, quad, poly, g, L=3):
    for lev in range(1,L+1):
        obj=level(steps,sq,refl,m,e,quad,poly,g,lev)
        for T in ('X','Y'):
            if overlaps(obj[T][0],poly): return False, lev, T
            if not solid(obj[T][0],poly): return False, lev, T+' holes'
    return True, L, None
if __name__=='__main__':
    import spectre_exact as SE
    sp=[(60,3,1),(0,2,0),(60,3,1),(60,3,1),(0,2,0),(60,3,1),(-120,3,3)]; sq=[(6,2),(5,1),(3,2),(0,1)]
    poly=[cx(p) for p in SE.P]; quad=[cx(p) for p in SE.Tile('x').quad]
    g=(Z, cx(SE.P[8]), 0)          # Gamma2 = trans(P[8]) * rot(30)
    print("control Spectre, levels 1-3:", valid(sp,sq,True,7,2,quad,poly,g,3))
    print("control with a wrong Mystic placement:", valid(sp,sq,True,7,2,quad,poly,(1+0j,cx(SE.P[8]),0),2))
