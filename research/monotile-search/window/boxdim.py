import numpy as np, json, sys
def window(prefix,L):
    X=np.load(f'{prefix}4d_L{L}.npy'); lab=json.load(open(f'{prefix}lab_L{L}.json'))
    X=X-X.mean(0); w,V=np.linalg.eigh(np.cov(X.T)); Y=X@V[:,:2]
    cls=np.unique(np.array([f'{a}|{b}|{c}' for a,b,c in lab]),return_inverse=True)[1]
    return Y,cls
def boundary_counts(Y,cls,ks):
    lo=Y.min(0); span=(Y.max(0)-lo).max()*1.0001; res=[]
    for k in ks:
        ij=np.floor((Y-lo)/span*k).astype(np.int64); cell=ij[:,0]*k+ij[:,1]
        order=np.lexsort((cls,cell)); c,s=cell[order],cls[order]
        # number of distinct classes per cell
        newcell=np.r_[True,c[1:]!=c[:-1]]; newcls=newcell|np.r_[True,s[1:]!=s[:-1]]
        ncls=np.add.reduceat(newcls.astype(int),np.flatnonzero(newcell))
        occ=newcell.sum(); res.append((k,occ,(ncls>=2).sum(),len(Y)/occ))
    return res
if __name__=='__main__':
    p,L=sys.argv[1],int(sys.argv[2]); Y,cls=window(p,L)
    ks=[8,12,16,24,32,48,64,96,128,192,256]
    R=boundary_counts(Y,cls,ks)
    for r in R: print('k=%4d occupied=%7d boundary=%7d pts/box=%.1f'%r)
    k=np.log([r[0] for r in R]); b=np.log([r[2] for r in R])
    for i in range(len(R)-2): print('local slope k=%d..%d: %.3f'%(R[i][0],R[i+2][0],(b[i+2]-b[i])/(k[i+2]-k[i])))
