"""Precompute the two simulations for long03 (symmetry): a Turing pattern and a cosmic web.

Turing: Schnakenberg reaction-diffusion, u_t = Du lap u + a - u + u^2 v, v_t = Dv lap v + b - u^2 v.
Starts at the uniform steady state plus 1% noise; diffusion (Dv >> Du) makes it unstable -> spots.
Cosmic web: particles start evenly spread; a smooth random potential with 1-part ripples; particles
fall down its gradient (Zel'dovich-style displacement grows with time) -> sheets, filaments, clumps.
"""
import numpy as np, os
from scipy.ndimage import gaussian_filter
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'long03')
rng = np.random.default_rng(1952)

# ---------- Turing
N = 160; a, b, Du, Dv = 0.1, 0.9, 1.0, 40.0
dt = 0.004
u = (a + b) * (1 + 0.01 * rng.standard_normal((N, N)))
v = b / (a + b) ** 2 * (1 + 0.01 * rng.standard_normal((N, N)))
def lap(z): return np.roll(z, 1, 0) + np.roll(z, -1, 0) + np.roll(z, 1, 1) + np.roll(z, -1, 1) - 4 * z
snaps = []; T_END = 60.0; steps = int(T_END / dt); every = steps // 90
for s in range(steps + 1):
    if s % every == 0: snaps.append(u.astype(np.float32).copy())
    uv = u * u * v
    u, v = u + dt * (Du * lap(u) + a - u + uv), v + dt * (Dv * lap(v) + b - uv)
snaps = np.array(snaps)
print('turing snaps', snaps.shape, 'range last', float(snaps[-1].min()), float(snaps[-1].max()), 'std first/last', float(snaps[0].std()), float(snaps[-1].std()))

# ---------- cosmic microwave-like field and web
G = 256
phi = gaussian_filter(rng.standard_normal((G, G)), 6, mode='wrap')
phi /= phi.std()
gy, gx = np.gradient(phi)
P = 26000
p0 = rng.uniform(0, G, (P, 2))
ix = p0.astype(int) % G
disp = np.stack([-gx[ix[:, 1], ix[:, 0]], -gy[ix[:, 1], ix[:, 0]]], 1)
cmb = gaussian_filter(rng.standard_normal((G, G)), 3, mode='wrap'); cmb /= np.abs(cmb).max()
np.savez_compressed(os.path.join(OUT, 'sims.npz'), turing=snaps, cmb=cmb.astype(np.float32),
                    p0=(p0 / G).astype(np.float32), disp=(disp / G).astype(np.float32))
print('saved')
