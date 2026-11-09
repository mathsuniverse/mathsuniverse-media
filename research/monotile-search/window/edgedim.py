import numpy as np, sys
from boxdim import window
def edge_counts(Z,ks):
    lo=Z.min(0); span=(Z.max(0)-lo).max()*1.0001; out=[]
    for k in ks:
        ij=np.floor((Z-lo)/span*k).astype(int)+1; G=np.zeros((k+2,k+2),bool); G[ij[:,0],ij[:,1]]=True
        nb=G[:-2,1:-1]&G[2:,1:-1]&G[1:-1,:-2]&G[1:-1,2:]
        occ=G[1:-1,1:-1]; edge=occ&~nb; out.append((k,occ.sum(),edge.sum(),len(Z)/occ.sum()))
    return out
if __name__=='__main__':
    p,L=sys.argv[1],int(sys.argv[2]); Y,cls=window(p,L)
    ks=[16,24,32,48,64,96,128,192]
    slopes=[]
    for c in np.unique(cls):
        Z=Y[cls==c]; R=[r for r in edge_counts(Z,ks) if r[3]>=6]
        if len(R)<4: continue
        k=np.log([r[0] for r in R]); e=np.log([r[2] for r in R])
        s=np.polyfit(k[-4:],e[-4:],1)[0]; slopes.append(s)
    slopes=np.array(slopes); print(p,'L',L,'classes',len(slopes),'fine-scale boundary slope: median %.3f  min %.3f  max %.3f'%(np.median(slopes),slopes.min(),slopes.max()))
