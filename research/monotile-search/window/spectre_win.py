import numpy as np, json
from spectre_exact import build, flatten
def units(n):
    lv=build(n); tiles,metas=flatten(lv[n]['Delta'],n)
    uid={}; ulist=[]; refs=[]; owner=[]
    for ti,(lab,k,f,ref,anc) in enumerate(tiles):
        if anc and metas[anc[-1]][0]==0: key=('m',anc[-1]); cls=(metas[anc[-1]][1],metas[anc[-1]][2],metas[anc[-1]][3]); up=anc[:-1]
        else: key=('t',ti); cls=(lab,k,f); up=anc
        if key not in uid: uid[key]=len(ulist); ulist.append([cls,[],up])
        ulist[uid[key]][1].append(ref)
    U=np.array([np.mean(u[1],axis=0) for u in ulist]); C=[u[0] for u in ulist]
    lev2=[i for i,m in enumerate(metas) if m[0]==2]; pos2={m:j for j,m in enumerate(lev2)}
    M2=np.zeros((len(lev2),4)); cnt=np.zeros(len(lev2)); anc2=[]
    for u_i,u in enumerate(ulist):
        a=[x for x in u[2] if metas[x][0]==2][0]; j=pos2[a]; anc2.append(j)
        M2[j]+=np.sum(u[1],axis=0); cnt[j]+=len(u[1])
    M2/=cnt[:,None]
    return U,C,M2,np.array(anc2),[metas[i] for i in lev2]
n=6
U6,C6,M26,anc6,lev2meta=units(n); U4,C4,_,_,_=units(n-2)
print('units L6',len(U6),'level-2 metas',len(M26),'units L4',len(U4))
print('label match',sum(1 for m,c in zip(lev2meta,C4) if m[1]==c[0]),'/',len(C4))
keys=sorted(set(C4)); Y=[];Zs=[]
for k in keys:
    idx=[i for i,c in enumerate(C4) if c==k]; Y.append(M26[idx]-M26[idx].mean(0)); Zs.append(U4[idx]-U4[idx].mean(0))
Y=np.vstack(Y); Zs=np.vstack(Zs); A=np.linalg.lstsq(Zs,Y,rcond=None)[0].T
print('A (double step) =\n',np.round(A,4),'\nresidual',np.sqrt(np.mean((Zs@A.T-Y)**2)))
ev=np.linalg.eigvals(A); print('eigenvalues',np.round(ev,6),' 4+-sqrt15 =',4+15**.5,4-15**.5)
lam=4-15**.5; w,V=np.linalg.eig(A.T); Lint=np.real(V[:,np.isclose(w,lam)]).T
x6=U6@Lint.T; x4=U4@Lint.T
maps={}
for i in range(len(U6)):
    j=anc6[i]; t=x6[i]-lam*x4[j]; maps.setdefault((C4[j],C6[i]),[]).append(t)
uniq={k:np.unique(np.round(np.array(v),7),axis=0) for k,v in maps.items()}
print('IFS maps',sum(len(v) for v in uniq.values()),'classes',len(set(C6)|set(C4)),'max distinct',max(len(v) for v in uniq.values()))
cls=sorted(set(C6)|set(C4))
json.dump({'k':lam,'classes':[list(c) for c in cls],'maps':[[list(p),list(c),t.tolist()] for (p,c),T in uniq.items() for t in T]},open('ifs_spectre.json','w'))
