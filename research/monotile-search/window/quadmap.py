"""The Spectre substitution as a linear map on quad edge vectors (THEORY s11-12)."""
import numpy as np, sympy as sp, sys
sys.argv=['x','0']
import spectre_exact as SE
class Q:
    def __init__(s,quad): s.quad=quad
def superquad(quad):
    sysd={n:Q(quad) for n in SE.NAMES}; sysd['Delta']=Q(quad)
    return SE.supertiles(sysd)['Delta'].quad
def edges(q): return np.concatenate([q[i+1]-q[i] for i in range(3)])
def quad_from_edges(e):
    q=[np.zeros(4,int)]
    for i in range(3): q.append(q[-1]+e[4*i:4*i+4])
    return q
M=np.zeros((12,12),int)
for j in range(12):
    e=np.zeros(12,int); e[j]=1
    M[:,j]=edges(superquad(quad_from_edges(e)))
# check linearity on the real Spectre quad
q0=SE.Tile('x').quad; assert (edges(superquad(q0))==M@edges(q0)).all()
x=sp.symbols('x')
print("single step charpoly:", sp.factor(sp.Matrix(M).charpoly(x).as_expr()))
print("double step charpoly:", sp.factor(sp.Matrix(M@M).charpoly(x).as_expr()))
np.save('quadmap_spectre.npy',M)
