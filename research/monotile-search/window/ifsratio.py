import numpy as np, sys, math
from ifsdim import build, points
from edgedim import edge_counts
path=sys.argv[1]; nmax=int(sys.argv[2]); cls=[int(x) for x in sys.argv[3].split(',')]
k,cl,into=build(path); names={v:k_ for k_,v in cl.items()}
for c in cls:
    Z,sc=points(k,into,c,nmax); span=(Z.max(0)-Z.min(0)).max()
    out=[]
    for n in range(nmax-5,nmax+1):
        kk=int(round(span/(k**n)/4))
        if kk<4: continue
        out.append((n,kk,edge_counts(Z,[kk])[0][2]))
    rat=[out[i+1][2]/out[i][2] for i in range(len(out)-1)]
    print(names[c],'edge boxes',[o[2] for o in out],'ratios',[round(r,3) for r in rat],'-> dim',[round(math.log(r)/math.log(1/k),3) for r in rat])
