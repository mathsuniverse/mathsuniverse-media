import sympy as sp
w=sp.Rational(1,2)+sp.sqrt(3)*sp.I/2
R=sp.Matrix([[0,-1],[1,1]])
def to2(M,perm):
    M=sp.Matrix(M).extract(perm,perm); out=sp.zeros(2,2)
    for i in range(2):
        for j in range(2):
            B=M[2*i:2*i+2,2*j:2*j+2]; a,b=B[0,0],B[1,0]
            assert B==a*sp.eye(2)+b*R; out[i,j]=a+b*w
    return out
H=to2([[2,1,-2,-2],[-1,1,2,0],[0,1,1,-1],[-1,-1,1,2]],[0,1,2,3])
S=to2([[4,4,-3,5],[1,4,-4,3],[3,-5,7,-1],[4,-3,5,1]],[0,2,1,3])   # (c0,c2 | c1,c3): a=c0+c2 w, b=c1+c3 w, v=a+b z
for n,M in (("hat",H),("spectre^2",S)):
    print(n, M.applyfunc(lambda e: sp.nsimplify(sp.expand(e))), " trace",sp.simplify(M.trace())," det",sp.simplify(sp.expand(M.det())))
    # left eigenvector f with f M = mu f  (physical / internal functionals)
    for ev in M.T.eigenvects():
        mu=sp.simplify(ev[0]); v=ev[2][0]; r=sp.simplify(v[1]/v[0])
        print("   mu=",mu, "~",sp.N(mu,6)," f(b)/f(a)=",sp.N(r,6)," |.|=",sp.N(sp.Abs(r),6)," arg deg=",sp.N(sp.arg(r)*180/sp.pi,6))
