import numpy as np, json, sys
from edgedim import edge_counts
def build(path):
    D=json.load(open(path)); k=D['k']; cl={tuple(c):i for i,c in enumerate(D['classes'])}
    into={}   # child class -> list of (parent idx, t)
    for p,c,t in D['maps']: into.setdefault(cl[tuple(c)],[]).append((cl[tuple(p)],np.array(t)))
    return k,cl,into
def points(k,into,c,n):
    cls=np.array([c]); off=np.zeros((1,2)); sc=1.0
    for d in range(n):
        nc=[];no=[]
        for ch,lst in into.items():
            m=cls==ch
            if not m.any(): continue
            for p,t in lst: nc.append(np.full(m.sum(),p)); no.append(off[m]+sc*t)
        cls=np.concatenate(nc); off=np.vstack(no); sc*=k
    return off, sc
if __name__=='__main__':
    path=sys.argv[1]; n=int(sys.argv[2]); k,cl,into=build(path)
    res=[]
    for c in range(len(cl)):
        Z,sc=points(k,into,c,n); span=(Z.max(0)-Z.min(0)).max()
        kmax=int(span/sc/3)
        ks=[int(kmax/2**(j/2)) for j in range(10,-1,-1)]
        R=edge_counts(Z,ks); kk=np.log([r[0] for r in R]); e=np.log([r[2] for r in R])
        s=np.polyfit(kk[-6:],e[-6:],1)[0]; res.append(s)
        if c<3: print('class',c,'points',len(Z),'boxes up to',ks[-1],'slopes', [round((e[i+2]-e[i])/(kk[i+2]-kk[i]),3) for i in range(0,len(R)-2,2)])
    res=np.array(res); print('boundary dimension estimate per class: median %.4f min %.4f max %.4f'%(np.median(res),res.min(),res.max()))
