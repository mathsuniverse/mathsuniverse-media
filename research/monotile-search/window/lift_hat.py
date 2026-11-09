import json, sys, numpy as np, math
from collections import deque
L=int(sys.argv[1])
H=json.load(open(f'hats_L{L}.json'))
hr3=math.sqrt(3)/2
hp=lambda x,y:(x+0.5*y, hr3*y)
O=[hp(*p) for p in [(0,0),(-1,-1),(0,-2),(2,-2),(2,-1),(4,-2),(5,-1),(4,0),(3,0),(2,2),(0,3),(0,2),(-1,2)]]
# split the length-2 edge
P=[]
for i in range(13):
    a,b=O[i],O[(i+1)%13]; P.append(a)
    if abs(math.dist(a,b)-2)<1e-9: P.append(((a[0]+b[0])/2,(a[1]+b[1])/2))
print('hat vertices after split',len(P), sorted(set(round(math.dist(P[i],P[(i+1)%len(P)]),6) for i in range(len(P)))))
xi=complex(0.5,hr3); w=math.sqrt(3)*complex(math.cos(math.pi/6),math.sin(math.pi/6))
def zxi(z):  # z = x + y*xi, integers
    y=z.imag/hr3; x=z.real-0.5*y; return (round(x),round(y)), abs(x-round(x))+abs(y-round(y))
key=lambda p:(round(p[0]*1e4),round(p[1]*1e4))
adj={}; tiles=[]
for t in H:
    lab,a,b,c,d,e,f=t
    vs=[key((a*x+b*y+c, d*x+e*y+f)) for x,y in P]
    tiles.append((lab,vs, round(math.degrees(math.atan2(d,a)))%360, a*e-b*d<0))
    for i in range(len(vs)):
        u,v=vs[i],vs[(i+1)%len(vs)]
        dz=complex(v[0]-u[0],v[1]-u[1])/1e4*2
        if abs(abs(dz)-1)<1e-3: (k,err)=zxi(dz); vec=(k[0],k[1],0,0)
        else: (k,err)=zxi(dz/w); vec=(0,0,k[0],k[1])
        assert err<1e-3, (dz,err)
        adj.setdefault(u,[]).append((v,vec)); adj.setdefault(v,[]).append((u,tuple(-q for q in vec)))
# BFS
pos={}; s=next(iter(adj)); pos[s]=np.zeros(4,int); dq=deque([s]); bad=0
while dq:
    u=dq.popleft()
    for v,vec in adj[u]:
        pv=pos[u]+np.array(vec)
        if v in pos:
            if (pos[v]!=pv).any(): bad+=1
        else: pos[v]=pv; dq.append(v)
print('vertices',len(pos),'inconsistent edges',bad)
# tile reference = mean of its vertices' 4D coords
out=[]
for lab,vs,rot,refl in tiles:
    m=np.mean([pos[v] for v in vs],axis=0); out.append((lab,rot,int(refl),*m))
np.save(f'hat4d_L{L}.npy',np.array([o[3:] for o in out])); json.dump([o[:3] for o in out],open(f'hatlab_L{L}.json','w'))
print('labels',sorted(set((o[0],o[1],o[2]) for o in out))[:40])
