"""Exact Spectre (Tile(1,1)) supertiles in Z[zeta12], replicating shrx/spectre's construction.
Numbers: 4-int vectors (a,b,c,d) = a + b z + c z^2 + d z^3, z = exp(i pi/6), z^4 = z^2 - 1."""
import numpy as np, sys, json, math
Z=np.array; MZ=np.array([[0,0,0,-1],[1,0,0,0],[0,1,0,1],[0,0,1,0]])   # multiply by z
MC=np.array([[1,0,1,0],[0,1,0,0],[0,0,-1,0],[0,-1,0,-1]])            # complex conjugation: z->z-z^3, z^2->1-z^2, z^3->-z^3
ROT=[np.linalg.matrix_power(MZ,k) for k in range(12)]
def cx(v): z=complex(math.cos(math.pi/6),math.sin(math.pi/6)); return v[0]+v[1]*z+v[2]*z**2+v[3]*z**3
class T:  # p -> rot^k (conj^f p) + t
    def __init__(s,k=0,f=0,t=None): s.k=k%12; s.f=f; s.t=np.zeros(4,int) if t is None else np.array(t)
    def ap(s,p): q=MC@p if s.f else p; return ROT[s.k]@q+s.t
    def lin(s,v): q=MC@v if s.f else v; return ROT[s.k]@q
    def __mul__(s,o):  # s after o
        if s.f: k=s.k-o.k; f=1-o.f
        else: k=s.k+o.k; f=o.f
        return T(k,f,s.ap(o.t))
I=T()
def rot(deg): return T(round(deg/30),0)
def trans(v): return T(0,0,v)
R=T(6,1)   # x -> -x : -conj(p) = z^6 conj(p)
# Spectre outline from its edge directions (shrx SPECTRE_POINTS), unit edges
P=[np.zeros(4,int)]
for d in [0,10,1,3,0,2,4,7,5,6,6,8,11,9][:-1]:
    pass
pts_f=[(0,0),(1.0,0.0),(1.5,-math.sqrt(3)/2),(1.5+math.sqrt(3)/2,0.5-math.sqrt(3)/2),(1.5+math.sqrt(3)/2,1.5-math.sqrt(3)/2),
 (2.5+math.sqrt(3)/2,1.5-math.sqrt(3)/2),(3+math.sqrt(3)/2,1.5),(3.0,2.0),(3-math.sqrt(3)/2,1.5),(2.5-math.sqrt(3)/2,1.5+math.sqrt(3)/2),
 (1.5-math.sqrt(3)/2,1.5+math.sqrt(3)/2),(0.5-math.sqrt(3)/2,1.5+math.sqrt(3)/2),(-math.sqrt(3)/2,1.5),(0.0,1.0)]
P=[np.zeros(4,int)]
for i in range(13):
    a,b=pts_f[i],pts_f[i+1]; ang=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])); k=round(ang/30)%12
    assert abs(math.hypot(b[0]-a[0],b[1]-a[1])-1)<1e-9
    P.append(P[-1]+ROT[k]@np.array([1,0,0,0]))
for p,q in zip(P,pts_f): assert abs(cx(p)-complex(*q))<1e-9
class Tile:
    def __init__(s,label): s.label=label; s.quad=[P[3],P[5],P[7],P[11]]
class Meta:
    def __init__(s,geoms,quad,label=None): s.geoms=geoms; s.quad=quad; s.label=label
NAMES=["Gamma","Delta","Theta","Lambda","Xi","Pi","Sigma","Phi","Psi"]
def base():
    b={n:Tile(n) for n in NAMES if n!='Gamma'}
    b['Gamma']=Meta([(Tile('Gamma1'),I),(Tile('Gamma2'),trans(P[8])*rot(30))],[P[3],P[5],P[7],P[11]],'Gamma')
    return b
RULES={"Gamma":["Pi","Delta",None,"Theta","Sigma","Xi","Phi","Gamma"],"Delta":["Xi","Delta","Xi","Phi","Sigma","Pi","Phi","Gamma"],
 "Theta":["Psi","Delta","Pi","Phi","Sigma","Pi","Phi","Gamma"],"Lambda":["Psi","Delta","Xi","Phi","Sigma","Pi","Phi","Gamma"],
 "Xi":["Psi","Delta","Pi","Phi","Sigma","Psi","Phi","Gamma"],"Pi":["Psi","Delta","Xi","Phi","Sigma","Psi","Phi","Gamma"],
 "Sigma":["Xi","Delta","Xi","Phi","Sigma","Pi","Lambda","Gamma"],"Phi":["Psi","Delta","Psi","Phi","Sigma","Pi","Phi","Gamma"],
 "Psi":["Psi","Delta","Psi","Phi","Sigma","Psi","Phi","Gamma"]}
def supertiles(sys_):
    quad=sys_['Delta'].quad
    rules=[[60,3,1],[0,2,0],[60,3,1],[60,3,1],[0,2,0],[60,3,1],[-120,3,3]]
    trs=[I]; tot=0; rotation=I; tq=list(quad)
    for ang,fr,to in rules:
        if ang: tot+=ang; rotation=rot(tot); tq=[rotation.ap(q) for q in quad]
        ttt=trans(trs[-1].ap(quad[fr])-tq[to]); trs.append(ttt*rotation)
    trs=[R*t for t in trs]
    sq=[trs[6].ap(quad[2]),trs[5].ap(quad[1]),trs[3].ap(quad[2]),trs[0].ap(quad[1])]
    return {lab:Meta([(sys_[s],t) for s,t in zip(subs,trs) if s],sq,lab) for lab,subs in RULES.items()}
def build(n):
    s=base(); levels=[s]
    for _ in range(n): s=supertiles(s); levels.append(s)
    return levels
def flatten(top,n,toplabel='Delta'):
    """returns tiles: (label, k, f, ref4d, ancestors list of (meta id)) and metas: id->(level,label,k,f)"""
    tiles=[]; metas=[]
    def rec(g,Tr,lev,anc,lab):
        if isinstance(g,Tile): tiles.append((g.label,Tr.k,Tr.f,Tr.ap(np.zeros(4,int)),anc)); return
        mid=len(metas); metas.append((lev,lab,Tr.k,Tr.f))
        for ch,t in g.geoms: rec(ch,Tr*t,lev-1,anc+[mid],getattr(ch,'label',None))
    rec(top,I,n,[],toplabel)
    return tiles,metas
if __name__=='__main__':
    n=int(sys.argv[1]); lv=build(n); tiles,metas=flatten(lv[n]['Delta'],n)
    print('level',n,'spectres',len(tiles),'metatiles',len(metas))
