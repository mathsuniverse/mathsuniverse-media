import json, numpy as np
def load(L):
    X=np.load(f'hat4d_L{L}.npy'); H=json.load(open(f'hats_L{L}.json')); M=json.load(open(f'meta_L{L}.json'))
    par=np.array([h[7] for h in H]); meta={m[0]:m for m in M}
    lev0=[m for m in M if m[1]==0]; lev1=[m for m in M if m[1]==1]
    id0={m[0]:i for i,m in enumerate(lev0)}; id1={m[0]:i for i,m in enumerate(lev1)}
    c0=np.zeros((len(lev0),4)); n0=np.zeros(len(lev0))
    i0=np.array([id0[p] for p in par]); np.add.at(c0,i0,X); np.add.at(n0,i0,1); 
    c1=np.zeros((len(lev1),4)); n1=np.zeros(len(lev1))
    p1=np.array([id1[meta[lev0[i][0]][4]] for i in i0]); np.add.at(c1,p1,X); np.add.at(n1,p1,1)
    c0/=n0[:,None]; c1/=n1[:,None]
    cls0=[(m[2],m[3]) for m in lev0]; cls1=[(m[2],m[3]) for m in lev1]
    par0=np.array([id1[m[4]] for m in lev0])
    return c0,cls0,c1,cls1,par0,lev0
c0a,cls0a,c1a,cls1a,par0a,lev0a=load(6)   # patch L=6
c0b,cls0b,_,_,_,_=load(5)                 # patch L=5
print('level-1 metatiles in L6:',len(c1a),' level-0 metatiles in L5:',len(c0b))
same=sum(1 for a,b in zip(cls1a,cls0b) if a[0]==b[0]); print('type match',same,'/',len(cls1a))
rot=set((a[1]-b[1])%360 for a,b in zip(cls1a,cls0b)); print('angle differences between levels:',rot)
# fit c1 = A c0 + b_class
keys=sorted(set(cls0b)); Y=[];Z=[]; 
for k in keys:
    idx=[i for i,c in enumerate(cls0b) if c==k]
    Y.append(c1a[idx]-c1a[idx].mean(0)); Z.append(c0b[idx]-c0b[idx].mean(0))
Y=np.vstack(Y); Z=np.vstack(Z); A,res,_,_=np.linalg.lstsq(Z,Y,rcond=None); A=A.T
print('A =\n',np.round(A,4)); print('residual rms',np.sqrt(np.mean((Z@A.T-Y)**2)))
print('eigenvalues',np.round(np.linalg.eigvals(A),6))
np.save('A_hat.npy',A)
