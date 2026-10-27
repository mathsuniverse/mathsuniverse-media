// Symmetry operations in fractional (lattice) coordinates, standard settings (International Tables).
// Each op is [a, b, c, d, tx, ty]: (x, y) -> (a x + b y + tx, c x + d y + ty).
// Lattice: basis vectors A, B in screen units (unit cell). Friezes repeat along x only.
(function (root) {
  const S3 = Math.sqrt(3);
  const op = (a, b, c, d, tx = 0, ty = 0) => [a, b, c, d, tx, ty];
  const I = op(1, 0, 0, 1);

  // ---------------------------------------------------------------- 7 frieze groups (Conway's names)
  const FRIEZES = [
    { id: 'p1',   conway: 'hop',             ops: [I] },
    { id: 'p11g', conway: 'step',            ops: [I, op(1, 0, 0, -1, .5, 0)] },
    { id: 'p1m1', conway: 'sidle',           ops: [I, op(-1, 0, 0, 1)] },
    { id: 'p2',   conway: 'spinning hop',    ops: [I, op(-1, 0, 0, -1)] },
    { id: 'p2mg', conway: 'spinning sidle',  ops: [I, op(-1, 0, 0, -1), op(-1, 0, 0, 1, .5, 0), op(1, 0, 0, -1, .5, 0)] },
    { id: 'p11m', conway: 'jump',            ops: [I, op(1, 0, 0, -1)] },
    { id: 'p2mm', conway: 'spinning jump',   ops: [I, op(-1, 0, 0, 1), op(1, 0, 0, -1), op(-1, 0, 0, -1)] },
  ];

  // ---------------------------------------------------------------- 17 wallpaper groups
  const P4 = [I, op(-1, 0, 0, -1), op(0, -1, 1, 0), op(0, 1, -1, 0)];
  const P3 = [I, op(0, -1, 1, -1), op(-1, 1, -1, 0)];
  const P6 = P3.concat([op(-1, 0, 0, -1), op(0, 1, -1, 1), op(1, -1, 1, 0)]);
  const M3A = [op(0, -1, -1, 0), op(-1, 1, 0, 1), op(1, 0, 1, -1)];   // p3m1 mirrors
  const M3B = [op(0, 1, 1, 0), op(1, -1, 0, -1), op(-1, 0, -1, 1)];   // p31m mirrors
  const centre = ops => ops.concat(ops.map(o => [o[0], o[1], o[2], o[3], o[4] + .5, o[5] + .5]));
  const PMM = [I, op(-1, 0, 0, -1), op(-1, 0, 0, 1), op(1, 0, 0, -1)];

  const SQ = { A: [1, 0], B: [0, 1] }, RECT = { A: [1, 0], B: [0, .72] }, HEX = { A: [1, 0], B: [-.5, S3 / 2] }, OBL = { A: [1, 0], B: [.32, .8] };
  const WALLPAPERS = [
    { id: 'p1',   lattice: OBL,  order: 1,  ops: [I] },
    { id: 'p2',   lattice: OBL,  order: 2,  ops: [I, op(-1, 0, 0, -1)] },
    { id: 'pm',   lattice: RECT, order: 2,  ops: [I, op(-1, 0, 0, 1)] },
    { id: 'pg',   lattice: RECT, order: 2,  ops: [I, op(-1, 0, 0, 1, 0, .5)] },
    { id: 'cm',   lattice: RECT, order: 2,  ops: centre([I, op(-1, 0, 0, 1)]) },
    { id: 'pmm',  lattice: RECT, order: 4,  ops: PMM },
    { id: 'pmg',  lattice: RECT, order: 4,  ops: [I, op(-1, 0, 0, -1), op(-1, 0, 0, 1, .5, 0), op(1, 0, 0, -1, .5, 0)] },
    { id: 'pgg',  lattice: RECT, order: 4,  ops: [I, op(-1, 0, 0, -1), op(-1, 0, 0, 1, .5, .5), op(1, 0, 0, -1, .5, .5)] },
    { id: 'cmm',  lattice: RECT, order: 4,  ops: centre(PMM) },
    { id: 'p4',   lattice: SQ,   order: 4,  ops: P4 },
    { id: 'p4m',  lattice: SQ,   order: 8,  ops: P4.concat([op(-1, 0, 0, 1), op(1, 0, 0, -1), op(0, 1, 1, 0), op(0, -1, -1, 0)]) },
    { id: 'p4g',  lattice: SQ,   order: 8,  ops: P4.concat([op(-1, 0, 0, 1, .5, .5), op(1, 0, 0, -1, .5, .5), op(0, 1, 1, 0, .5, .5), op(0, -1, -1, 0, .5, .5)]) },
    { id: 'p3',   lattice: HEX,  order: 3,  ops: P3 },
    { id: 'p3m1', lattice: HEX,  order: 6,  ops: P3.concat(M3A) },
    { id: 'p31m', lattice: HEX,  order: 6,  ops: P3.concat(M3B) },
    { id: 'p6',   lattice: HEX,  order: 6,  ops: P6 },
    { id: 'p6m',  lattice: HEX,  order: 12, ops: P6.concat(M3A, M3B) },
  ];

  // rosettes: cyclic C_n and dihedral D_n as screen-space rotations/reflections about the origin
  function rosette(n, mirrors) {
    const out = [];
    for (let k = 0; k < n; k++) {
      const t = 2 * Math.PI * k / n, c = Math.cos(t), s = Math.sin(t);
      out.push([c, -s, s, c, 0, 0]);
      if (mirrors) { const c2 = Math.cos(2 * Math.PI * k / n), s2 = Math.sin(2 * Math.PI * k / n); out.push([c2, s2, s2, -c2, 0, 0]); }
    }
    return out;
  }
  const apply = (o, x, y) => [o[0] * x + o[1] * y + o[4], o[2] * x + o[3] * y + o[5]];
  root.SYM = { FRIEZES, WALLPAPERS, rosette, apply };
})(typeof window !== 'undefined' ? window : globalThis);
