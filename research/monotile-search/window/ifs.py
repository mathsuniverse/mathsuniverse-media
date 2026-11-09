import numpy as np, json
from infl import load
A=np.load('A_hat.npy'); phi=(1+5**.5)/2
w,V=np.linalg.eig(A.T); Lint=np.real(V[:,np.isclose(w,phi**-2)]).T   # left eigenvectors -> internal coords
c0a,cls0a,c1a,cls1a,par0a,_=load(6); c0b,cls0b,_,_,_,_=load(5)
xa=c0a@Lint.T; xb=c0b@Lint.T; k=phi**-2
maps={}
for i in range(len(c0a)):
    j=par0a[i]; t=xa[i]-k*xb[j]; key=(cls0b[j],cls0a[i])
    maps.setdefault(key,[]).append(t)
uniq={}
for key,ts in maps.items():
    ts=np.array(ts); r=np.unique(np.round(ts,7),axis=0); uniq[key]=r
nmaps=sum(len(v) for v in uniq.values()); classes=sorted(set(cls0a)|set(cls0b))
print('classes',len(classes),'IFS maps',nmaps,'max distinct per (parent,child)',max(len(v) for v in uniq.values()))
json.dump({'k':k,'classes':[list(c) for c in classes],'maps':[[list(p),list(c),t.tolist()] for (p,c),T in uniq.items() for t in T]},open('ifs_hat.json','w'))
