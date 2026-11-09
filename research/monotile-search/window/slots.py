# Eisenstein integers as pairs (x,y) = x + y w, w^2 = w - 1
import itertools, math, cmath
W=complex(0.5,math.sqrt(3)/2)
def mul(p,q): a,b=p; c,d=q; return (a*c-b*d, a*d+b*c+b*d)
def sub(p,q): return (p[0]-q[0],p[1]-q[1])
def N(p): a,b=p; return a*a+a*b+b*b
def cx(p): return p[0]+p[1]*W
def divmod_(p,q):
    z=cx(p)/cx(q); y=round(z.imag/W.imag); x=round(z.real-y*W.real)
    best=None
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            k=(x+dx,y+dy); r=sub(p,mul(q,k))
            if best is None or N(r)<N(best[1]): best=(k,r)
    return best
def gcd(p,q):
    while N(q): p,q=q,divmod_(p,q)[1]
    return p
def content(T):
    (a,b),(c,d)=T; return N(gcd(gcd(b,c),sub(a,d)))
hat=(((2,-1),(-2,2)),((0,-1),(1,1))); spec=(((4,3),(4,-5)),((1,4),(4,-3)))
print("content norm: hat",content(hat)," spectre^2",content(spec))
def sqf(n):
    f=1;m=n;p=2
    while p*p<=m:
        while m%(p*p)==0: m//=p*p; f*=p
        p+=1
    return m,f
# enumerate small T with trace s, det 1: T=[[a,b],[c,s-a]]
R=4; elts=[(x,y) for x in range(-R,R+1) for y in range(-R,R+1)]
for s in range(3,16):
    D,f=sqf(s*s-4); mu=(s+math.sqrt(s*s-4))/2
    own = "own field of 12-fold (excluded by P2)" if D==3 else ""
    found={}
    for a in elts:
        bc=sub(mul(a,sub((s,0),a)),(1,0))
        for b in elts:
            if N(b)==0: continue
            q,r=divmod_(bc,b)
            if N(r)==0 and max(abs(q[0]),abs(q[1]))<=R:
                T=((a,b),(q,sub((s,0),a))); g=content(T)
                if g not in found or sum(map(N,(a,b,q)))<found[g][0]: found[g]=(sum(map(N,(a,b,q))),T)
    print(f"s={s:2d} mu={mu:8.4f} Q(sqrt{D}) {own}  contents found (norm): {sorted(found)}")
    for g,(_,T) in sorted(found.items()):
        (a,b),(c,d)=T; m=cx(a)+cx(d); 
        # left eigenvector f=(1,r): f T = mu f  ->  a + r c = mu  -> r=(mu-a)/c ; need c!=0
        if N(c)==0: continue
        r=(mu-cx(a))/cx(c)
        print(f"     g-norm {g}: T=[[{a},{b}],[{c},{d}]]  eigen-geometry f(b)/f(a): |r|={abs(r):.4f} arg={math.degrees(cmath.phase(r)):7.2f}")
