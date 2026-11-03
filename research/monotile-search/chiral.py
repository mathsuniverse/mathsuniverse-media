"""The Spectre rule: re-test every shape that tiles periodically WITH mirrors, now with mirror images forbidden.
A shape that jams with mirrors also jams without them (fewer placements), so only PERIODIC shapes can change.
Mirror-symmetric shapes are unaffected (their mirror image is a rotation). Outcome per chiral shape:
PERIODIC (still repeats with rotations only), STUCK (needs mirrors to tile at all), or OPEN (candidate: tiles only aperiodically
without mirrors, like Tile(1,1) -> Spectre)."""
import gzip, json, os

HERE = os.path.dirname(os.path.abspath(__file__))


def stream_records(path, want=b'PERIODIC'):
    """Records of a big gzipped JSON array, read piece by piece (silverkite15 has 2.4 million); only those containing
    `want` are parsed. Records are flat objects (no nested {}), so braces mark their ends."""
    buf = b''
    with gzip.open(path, 'rb') as f:
        while True:
            chunk = f.read(1 << 22)
            if not chunk:
                break
            buf += chunk
            start = 0
            while True:
                a = buf.find(b'{', start)
                if a < 0:
                    buf = b''; break
                b = buf.find(b'}', a)
                if b < 0:
                    buf = buf[a:]; break
                rec = buf[a:b + 1]
                if want in rec:
                    yield json.loads(rec)
                start = b + 1
            else:
                pass


def load_periodic():
    """(grid, cells) for every PERIODIC shape in the stored results (local sieves, Modal sieves, silver families)."""
    out = []
    R = os.path.join(HERE, 'results')
    for fn in sorted(os.listdir(R)):
        if fn.endswith('_shapes.json.gz'):
            grid = fn[:-len('_shapes.json.gz')]
            data = json.load(gzip.open(os.path.join(R, fn), 'rt'))
            recs = [r for v in data.values() for r in v] if isinstance(data, dict) else data
            out += [(grid, r['cells']) for r in recs if r.get('cls') == 'PERIODIC']
    M = os.path.join(R, 'modal')
    if os.path.isdir(M):
        for fn in sorted(os.listdir(M)):
            if fn.endswith('_shapes.json.gz'):
                grid = fn[:-len('_shapes.json.gz')].rstrip('0123456789')
                for r in stream_records(os.path.join(M, fn)):
                    if r.get('cls') == 'PERIODIC':
                        out.append((grid, r['cells']))
    for fn in ('silver_families12.json', 'silver_families14.json'):
        p = os.path.join(R, fn)
        if os.path.exists(p):
            out += [('silverkite', r['cells']) for r in json.load(open(p)) if r['cls'] == 'PERIODIC']
    seen, uniq = set(), []
    for g, c in out:
        k = (g, tuple(map(tuple, c)))
        if k not in seen:
            seen.add(k); uniq.append((g, c))
    return uniq


def test_chunk(items, tcap=12, rcap=6, tcap2=24, rcap2=8):
    import engine as E, grids as G
    res = []
    for grid, cells in items:
        g = G.get(grid)
        cs = [tuple(c) for c in cells]
        sh = E.Shape(g, cs, chiral=True)
        if sh.achiral:
            res.append(dict(grid=grid, cells=cells, cls='achiral')); continue
        r = E.classify(g, cs, tcap=tcap, rcap=rcap, chiral=True, time_limit=300)
        if r['cls'] == 'OPEN':
            r = E.classify(g, cs, tcap=tcap2, rcap=rcap2, tmin=r.get('tori_complete_upto') or tcap, rmin=rcap,
                           chiral=True, time_limit=900)
        res.append(dict(grid=grid, cells=cells, n=len(cells), cls=r['cls'], fail_R=r.get('fail_R'),
                        tiles=r.get('tiles_per_domain')))
    return res
