"""Step A of the construction route (THEORY s12): chain rules -> operator -> slot.
A rule glues k copies of a 4-point quad: copy i+1 is turned by a total angle and its vertex `to` is placed on vertex
`fr` of copy i (as in the Spectre). The super-quad is 4 chosen vertices of chosen copies, optionally followed by the
reflection R (x -> -conj x). Everything is linear in the quad, so the rule is a 16x16 integer matrix S on the stacked
quad points; its eigenvalues give the slot."""
import numpy as np, itertools, math, sys, json
import spectre_exact as SE
ROT=[np.array(r) for r in SE.ROT]; RM=np.array(SE.MC); Rref=ROT[6]@RM
E=[np.zeros((4,16),int) for _ in range(4)]
for v in range(4): E[v][:,4*v:4*v+4]=np.eye(4,dtype=int)
def rule_matrix(steps, sq, refl):
    rots=[ROT[0]]; Ls=[np.zeros((4,16),int)]; tot=0
    for ang,fr,to in steps:
        tot=(tot+ang)%360; Rm=ROT[(tot//30)%12]
        Ls.append(rots[-1]@E[fr]+Ls[-1]-Rm@E[to]); rots.append(Rm)
    S=np.vstack([rots[i]@E[v]+Ls[i] for i,v in sq])
    if refl: S=np.kron(np.eye(4,dtype=int),Rref)@S
    return S
def slot_of(S):
    ev=np.linalg.eigvals(S.astype(float)); out=set()
    for z in ev:
        if abs(z.imag)>1e-7 or z.real<=1+1e-7: continue
        for p,lab in ((1,'single'),(2,'double')):
            s=z.real**p+z.real**-p
            if abs(s-round(s))<1e-6 and round(s)>=3: out.add((round(s),lab))
    return sorted(out)
if __name__=='__main__':
    # control: the Spectre rule
    sp_steps=[(60,3,1),(0,2,0),(60,3,1),(60,3,1),(0,2,0),(60,3,1),(-120,3,3)]
    S=rule_matrix(sp_steps,[(6,2),(5,1),(3,2),(0,1)],True)
    print("control Spectre rule:", slot_of(S), flush=True)
    k=int(sys.argv[1]); refls=(True,False)
    angs=[0,60,-60,120,-120,180]; glue=[(3,1),(2,0),(3,3),(1,3),(0,2),(1,1)]
    found={}; n=0
    for steps in itertools.product([(a,f,t) for a in angs for f,t in glue],repeat=k-1):
        for idx in itertools.combinations(range(k-1,-1,-1),4):
            for vs in itertools.product((1,2),repeat=4):
                sq=list(zip(idx,vs))
                for refl in refls:
                    n+=1
                    for sl in slot_of(rule_matrix(steps,sq,refl)):
                        if sl not in found: found[sl]=dict(steps=steps,sq=sq,refl=refl,count=0); print(k,sl,steps,sq,refl,flush=True)
                        found[sl]['count']+=1
    print("k",k,"rules tried",n)
    for sl,v in sorted(found.items()): print(sl, v['count'], v['steps'], v['sq'], v['refl'])
    json.dump({f"{a}_{b}":dict(v,steps=[list(x) for x in v['steps']]) for (a,b),v in found.items()},open(f'chainrules_k{k}.json','w'))
