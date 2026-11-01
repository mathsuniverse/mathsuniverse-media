"""Write RESULTS.md from results.json (+ validation.json, escalation.json if present)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Joseph Myers, polyomino.org.uk/mathematics/polyform-tiling (grid-aligned tilings):
# n: (tilers incl. aperiodic, non-tilers incl. those with holes)
MYERS = {1: (1, 0), 2: (1, 1), 3: (4, 0), 4: (5, 5), 5: (1, 26), 6: (71, 14), 7: (55, 207),
         8: (40, 833), 9: (755, 2162), 10: (15, 9996)}


def main():
    res = json.load(open(os.path.join(HERE, 'results.json')))
    val = json.load(open(os.path.join(HERE, 'validation.json'))) if os.path.exists(
        os.path.join(HERE, 'validation.json')) else []
    esc = json.load(open(os.path.join(HERE, 'escalation.json'))) if os.path.exists(
        os.path.join(HERE, 'escalation.json')) else {}
    L = ['# Results', '',
         '"candidate" = covers every disc up to the radius cap, but **no periodic (torus) tiling '
         'found up to the cap**. It is not a proof of aperiodicity; see README.md.', '']
    ns = sorted(int(n) for n in res)
    cfg = res[str(ns[0])]['config']
    L += [f"Caps: torus fundamental domain <= {cfg['tcap']} tiles; disc radius <= {cfg['rcap']} "
          f"hexagon spacings; Heesch tested up to {cfg['kmax']} coronas. All placements on the kite grid.", '',
          '| n | shapes | does not tile | tiles periodically | candidate | Myers: tilers / non-tilers | match | wall time |',
          '|---|---|---|---|---|---|---|---|']
    for n in ns:
        r = res[str(n)]
        c = r['counts']
        nt, pe, ca = c.get('no_tile', 0), c.get('periodic', 0), c.get('candidate', 0)
        my = MYERS.get(n)
        match = '' if my is None else ('yes' if (pe + ca, nt) == my else 'NO')
        L.append(f"| {n} | {len(r['shapes'])} | {nt} | {pe} | {ca} | "
                 f"{'' if my is None else f'{my[0]} / {my[1]}'} | {match} | {r['wall_time']}s |")
    L += ['', '"match" compares (periodic + candidate, does-not-tile) with Joseph Myers\' independent counts '
          '(his tiler count includes the hat at n=8 and the turtle at n=10).', '',
          '## Heesch numbers of the non-tilers', '',
          '| n | ' + ' | '.join(f'H={k}' for k in range(cfg['kmax'] + 1)) + ' |',
          '|---|' + '---|' * (cfg['kmax'] + 1)]
    for n in ns:
        hh = res[str(n)].get('heesch_hist', {})
        L.append(f'| {n} | ' + ' | '.join(str(hh.get(str(k), 0) + hh.get(f'{k}+', 0)) for k in range(cfg['kmax'] + 1)) + ' |')
    best = []
    for n in ns:
        for s in res[str(n)]['shapes']:
            if s.get('heesch') is not None:
                best.append((s['heesch'], s['id']))
    mx = max(best)[0] if best else None
    L += ['', f'Highest Heesch number found: {mx} ({", ".join(i for h, i in best if h == mx)}).',
          'Heesch here forbids holes in every corona (Kaplan\'s H_c). The values are not compared '
          'with any published polykite table; each corona structure is re-checked by independent code.', '']
    for h, i in best:
        if h == mx and os.path.exists(os.path.join(HERE, 'heesch', i + '.png')):
            L += [f'![{i}](heesch/{i}.png)', '']
    L += [
          '## Candidates', '']
    for n in ns:
        for s in res[str(n)]['shapes']:
            if s['cls'] == 'candidate':
                tag = ' — **the hat**' if s['is_hat'] else ' — **the turtle**' if s['is_turtle'] else ''
                L.append(f"### {s['id']} ({n} kites){tag}")
                L.append(f"Covers discs up to R={s['max_cover_R']}; no torus tiling with <= {cfg['tcap']} "
                         f"tiles per fundamental domain.")
                if s['id'] in esc:
                    L.append(f"Escalation: {esc[s['id']]}")
                L += ['', f"![{s['id']}](candidates/{s['id']}.png)", '']
    # cap sensitivity: which shapes would have been (false) candidates under smaller caps
    L += ['## How the caps affect the result', '',
          'Every shape that tiles periodically was found with a fundamental domain of at most the number '
          'of tiles below, and every non-tiler failed at the disc radius below. A shape becomes a (false) '
          'candidate if the torus cap is below the tiles it needs, or if the disc cap is below the radius at which it fails.', '',
          '| n | most tiles per period needed | largest failing disc radius |', '|---|---|---|']
    allsh = []
    for n in ns:
        sh = res[str(n)]['shapes']
        allsh += sh
        tp = [s['tiles_per_domain'] for s in sh if s['cls'] == 'periodic']
        fr = [s['fail_R'] for s in sh if s['cls'] == 'no_tile']
        L.append(f"| {n} | {max(tp) if tp else '-'} | {max(fr) if fr else '-'} |")
    big = [s['id'] for s in allsh if s['cls'] == 'periodic' and s['tiles_per_domain'] >= 12]
    L += ['', f"Shapes needing 12 tiles per period: {', '.join(big)}. With a torus cap below 12 they would "
          "show up as false candidates. Minimum periods come in whole hexagons, so an n-kite shape needs "
          "a multiple of 6/gcd(n,6) tiles per period (e.g. 6 for n = 7, 3 for n = 8 or 10, 2 for n = 9).", '']
    L += ['', '| torus cap (tiles) | disc cap (R) | candidates (n<=%d) |' % ns[-1], '|---|---|---|']
    for t, r in [(1, 6), (3, 6), (6, 6), (11, 6), (12, 2), (12, 3), (12, 4), (12, 5), (12, 6)]:
        c = sum(1 for s in allsh if s['cls'] == 'candidate'
                or (s['cls'] == 'periodic' and s['tiles_per_domain'] > t)
                or (s['cls'] == 'no_tile' and s['fail_R'] > r))
        L.append(f'| {t} | {r} | {c} |')
    L += ['', '(Rows other than the last are worked out from the recorded minimum period size / failing '
          'radius, not re-run.)', '']
    if val:
        L += ['## Validation (validate.py)', '', '| shape | kites | largest disc covered (R, kites) | periodic search | result |',
              '|---|---|---|---|---|']
        for v in val:
            okc = [c for c in v['cover'] if c['covered']]
            lc = f"R={okc[-1]['R']} ({okc[-1]['kites_in_disc']} kites)" if okc else 'none'
            p = v['periodic']
            pr = (f"<= {p['tcap_tiles_per_domain']} tiles/domain ({p['lattice_classes_tried']} lattices, "
                  f"{p['seconds']}s)")
            fnd = 'none found' if p['found'] is None else f"periodic, {p['found']['tiles_per_domain']} tile(s)/domain"
            L.append(f"| {v['name']} | {v['n']} | {lc} | {pr} | {fnd} |")
    open(os.path.join(HERE, 'RESULTS.md'), 'w').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
