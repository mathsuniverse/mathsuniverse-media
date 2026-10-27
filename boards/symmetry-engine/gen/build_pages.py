"""Generate SEO pattern pages for Symmetry Engine: 17 wallpaper groups + 7 frieze groups + index + worksheet.
Facts: identification rules are the standard ones; examples quoted from the Wikipedia 'Wallpaper group' article
(checked 27 Oct 2026) plus the regular square (p4m) and hexagonal/honeycomb (p6m) tilings."""
import os, json, html
OUT = os.path.join(os.path.dirname(__file__), '..', 'patterns')
FREE = {'p1', 'p4m', 'p6m'}
WP = [
 ('p1','o','Only slides. No turns, no mirrors, no glides: the motif just repeats along two directions.','Every copy faces exactly the same way.','Printed fabric or wrapping paper with a lopsided motif; computer-generated repeats.'),
 ('p2','2222','Half-turns only: the pattern looks the same upside down about many points, but has no mirrors or glides.','Turn the page upside down: it still matches. No mirror line anywhere.','Cloth from Hawaii, a US wire fence, an Egyptian mat.'),
 ('pm','**','Mirror lines in one direction only, all parallel. No turns.','Fold along one family of parallel lines and the halves match.','Egyptian tomb dress patterns; Indian metalwork shown at the Great Exhibition, 1851.'),
 ('pg','xx','Glides in one direction only: reflect and slide. No mirrors, no turns.','Copies alternate left- and right-facing, but always shifted, like footprints.','Herringbone patterns, for example a herringbone pavement in Salzburg.'),
 ('cm','*x','Mirrors in one direction, with glide lines halfway between them. No turns.','Parallel mirrors, and the rows are staggered.','Houndstooth textile; Egyptian dress and dado patterns.'),
 ('pmm','*2222','Mirrors in two perpendicular directions; every half-turn centre sits where mirrors cross.','A grid of mirror lines, like a window lattice.','A lattice fence; a mummy case in the Louvre; the colour filter of Fujifilm X-Trans sensors.'),
 ('pmg','22*','Mirrors in one direction, half-turn centres that are not on the mirrors, and glides at right angles to the mirrors.','Mirror lines one way, and upside-down pairs between them.','Floor tiling in Prague; cloth from Hawaii; a pentagon packing.'),
 ('pgg','22x','Glides in two perpendicular directions and half-turns, but no mirrors.','It feels symmetric, yet no fold line works: every match needs a slide.','Some tilings of hexagons and triangles; computer-generated designs.'),
 ('cmm','2*22','Mirrors in two perpendicular directions, plus half-turn centres that are not on the mirrors.','Like pmm, but with every other row shifted, as in brickwork.','A brick wall in running bond; a Turkish dish.'),
 ('p4','442','Quarter-turns, no mirrors: a pinwheel feel.','Turn by 90° about some points and it matches, but every corner swirls one way.','Viennese cane weaving; Renaissance earthenware.'),
 ('p4m','*442','Quarter-turns and mirrors in four directions; every quarter-turn centre sits on mirrors.','The symmetry of a sheet of square graph paper.','Square floor tiles and graph paper; a storm drain grating; the Cathedral of Bourges.'),
 ('p4g','4*2','Quarter-turns and mirrors in two directions, but the quarter-turn centres are not on the mirrors.','Pinwheels of four, arranged so that mirror lines run between them.','Bathroom linoleum; painted Chinese porcelain; fly screens.'),
 ('p3','333','Third-turns only, no mirrors.','Three-way swirls with no fold lines.','The snub trihexagonal tiling (ignoring colours); computer-generated designs.'),
 ('p3m1','*333','Third-turns and mirrors; every third-turn centre sits on mirrors.','Triangles of mirrors meeting at every three-fold point.','A Persian ornament; triangular and hexagonal tilings once coloured.'),
 ('p31m','3*3','Third-turns and mirrors, with some third-turn centres off the mirrors.','Mirror triangles plus extra three-fold swirls in their middles.','Chinese painting; a folding camping table design; packings of two sizes of circle.'),
 ('p6','632','Sixth-turns, no mirrors.','Six-way swirls, like a snowflake that has been twisted.','A Persian ornament; computer-generated designs.'),
 ('p6m','*632','Sixth-turns and mirrors in six directions: the richest wallpaper.','The symmetry of a honeycomb.','The honeycomb (hexagonal tiling); compact packings of two sizes of circle.'),
]
FR = [
 ('hop','p1','Only slides along the strip.','Every copy faces the same way: L L L L.'),
 ('step','p11g','A glide: reflect across the centre line and slide half a step.','Footprints when you walk: left, right, left, right.'),
 ('sidle','p1m1','Mirror lines across the strip.','A A A A, or footprints when you sidestep.'),
 ('spinning-hop','p2','Half-turns about points on the centre line.','N N N N, or S S S S.'),
 ('spinning-sidle','p2mg','Mirrors across the strip, half-turns between them, and a glide.','V Λ V Λ, a zigzag of alternating marks.'),
 ('jump','p11m','A mirror along the centre line of the strip.','D D D D, or B B B B: jumping with both feet.'),
 ('spinning-jump','p2mm','Mirrors along and across the strip, and half-turns where they meet.','H H H H, or X X X X.'),
]
COST = {'o':48,'*':24,'x':24}
def cost24(sig):
    tot, star, parts = 0, False, []
    for ch in sig:
        if ch == 'o': tot += 48; parts.append('o $2')
        elif ch == '*': tot += 24; star = True; parts.append('* $1')
        elif ch == 'x': tot += 24; parts.append('x $1')
        else:
            n = int(ch)
            c = 12*(n-1)//n if star else 24*(n-1)//n
            from math import gcd
            g = gcd(c, 24); parts.append(f"{'corner' if star else 'turn'} {n} ${c//g}/{24//g}")
            tot += c
    return tot, parts
for gid, sig, *_ in WP:
    assert cost24(sig)[0] == 48, (gid, sig)

CSS = open(os.path.join(os.path.dirname(__file__), 'page.css')).read()
def page(title, desc, body, script, canonical):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="https://symmetryengine.space{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;1,6..72,500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style></head><body>
<header class="top"><div class="wrap"><a class="brand" href="/">Symmetry <span>Engine</span></a><nav><a href="/patterns/">All 24 patterns</a><a href="/#wallpaper">Draw</a><a href="/vip/">VIP</a></nav></div></header>
<main class="wrap">{body}</main>
<footer class="wrap">Symmetry Engine · part of <a href="https://interactiveexplorer.space/">Interactive Explorer</a> · videos by <a href="https://interactiveexplorer.space/math-universe">The Math Universe</a></footer>
<script src="/groups.js"></script><script>{script}</script></body></html>'''

DRAW_JS = open(os.path.join(os.path.dirname(__file__), 'pattern.js')).read()
os.makedirs(OUT, exist_ok=True)
ids = [w[0] for w in WP]
for i, (gid, sig, what, spot, ex) in enumerate(WP):
    tot, parts = cost24(sig)
    prev, nxt = ids[i-1], ids[(i+1) % len(ids)]
    free = gid in FREE
    body = f'''<p class="eyebrow"><a href="/patterns/">Wallpaper patterns</a> · {i+1} of 17</p>
<h1>The <em>{gid}</em> wallpaper pattern</h1>
<p class="lede">{what}</p>
<div class="bench"><div class="box"><canvas id="cv" aria-label="A wallpaper pattern with symmetry group {gid}"></canvas></div>
<div class="side">
<div class="card"><h2>How to spot it</h2><p>{spot}</p></div>
<div class="card"><h2>Where you see it</h2><p>{ex}</p></div>
<div class="card"><h2>Conway's code: <code>{sig}</code></h2><p class="mono">{' + '.join(parts)} = $2</p><p class="note">Every wallpaper code costs exactly $2. <a href="/#magic">Why?</a></p></div>
<div class="card">{'<p>This pattern is free to draw with.</p><a class="btn primary" href="/#wallpaper">Draw your own '+gid+'</a>' if free else '<p>Drawing your own '+gid+' wallpaper is part of Symmetry Engine VIP.</p><a class="btn gold" href="/vip/">Unlock all 17</a>'}</div>
</div></div>
<nav class="pn"><a href="/patterns/wallpaper/{prev}/">← {prev}</a><a href="/patterns/">All patterns</a><a href="/patterns/wallpaper/{nxt}/">{nxt} →</a></nav>'''
    js = DRAW_JS + f"\nrenderWallpaper('{gid}');"
    d = os.path.join(OUT, 'wallpaper', gid); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w').write(page(f'{gid} wallpaper group: how to spot it, examples | Symmetry Engine',
        f'The {gid} wallpaper group ({sig}): {what} How to recognise it, real examples, and a live pattern you can explore.', body, js, f'/patterns/wallpaper/{gid}/'))
fids = [f[0] for f in FR]
for i, (slug, gid, what, spot) in enumerate(FR):
    name = slug.replace('-', ' ')
    prev, nxt = fids[i-1], fids[(i+1) % len(fids)]
    body = f'''<p class="eyebrow"><a href="/patterns/">Frieze patterns</a> · {i+1} of 7</p>
<h1>The <em>{name}</em> frieze ({gid})</h1>
<p class="lede">{what}</p>
<div class="box strip"><canvas id="cv" aria-label="A frieze pattern of type {name}"></canvas></div>
<div class="grid2"><div class="card"><h2>How to spot it</h2><p>{spot}</p></div>
<div class="card"><h2>Draw your own</h2><p>All seven friezes are free in Symmetry Engine.</p><a class="btn primary" href="/#friezes">Draw a {name} frieze</a></div></div>
<nav class="pn"><a href="/patterns/frieze/{prev}/">← {prev.replace('-',' ')}</a><a href="/patterns/">All patterns</a><a href="/patterns/frieze/{nxt}/">{nxt.replace('-',' ')} →</a></nav>'''
    js = DRAW_JS + f"\nrenderFrieze('{gid}');"
    d = os.path.join(OUT, 'frieze', slug); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w').write(page(f'The {name} frieze pattern ({gid}): one of the 7 frieze groups | Symmetry Engine',
        f'The {name} frieze ({gid}): {what} {spot} See it live.', body, js, f'/patterns/frieze/{slug}/'))
# index
cards = ''.join(f'<a class="tile" href="/patterns/wallpaper/{g}/"><canvas data-wp="{g}"></canvas><b>{g}</b><span>{s}</span></a>' for g, s, *_ in WP)
fcards = ''.join(f'<a class="tile wide" href="/patterns/frieze/{s}/"><canvas data-fr="{g}"></canvas><b>{s.replace("-"," ")}</b><span>{g}</span></a>' for s, g, *_ in FR)
body = f'''<p class="eyebrow">Symmetry Engine · the complete catalogue</p><h1>All <em>24</em> repeating patterns</h1>
<p class="lede">Every repeating pattern along a strip is one of 7 friezes. Every repeating pattern across a wall is one of 17 wallpapers. Pick one to see how to recognise it and where it appears.</p>
<h2 class="sec">The 7 friezes</h2><div class="tiles fr">{fcards}</div>
<h2 class="sec">The 17 wallpapers</h2><div class="tiles">{cards}</div>
<p class="note"><a href="/patterns/worksheet/">Printable classroom sheet</a></p>'''
open(os.path.join(OUT, 'index.html'), 'w').write(page('The 7 frieze and 17 wallpaper patterns: complete visual catalogue | Symmetry Engine',
    'All 24 repeating patterns, each drawn live: the 7 frieze groups and the 17 wallpaper groups, with how to spot each one and real examples.', body, DRAW_JS + "\nrenderTiles();", '/patterns/'))
# worksheet (print)
ws_ids = ['p1','pm','p2','p4m','p6m','cmm']
tiles = ''.join(f'<div class="ws"><canvas data-wp="{g}" data-ws="1"></canvas><p>Pattern {chr(65+i)}: mirrors? turns (which)? glides? Which group? ________</p></div>' for i, g in enumerate(ws_ids))
body = f'''<p class="eyebrow noprint"><a href="/patterns/">Patterns</a> · classroom sheet</p><h1>Name the pattern</h1>
<p class="lede">For each pattern, look for mirror lines, turning points and glides, then name its group. Answers at the bottom (fold them under before printing!).</p>
<button class="btn primary noprint" onclick="print()">Print this sheet</button>
<div class="wsgrid">{tiles}</div>
<p class="answers">Answers: A p1 · B pm · C p2 · D p4m · E p6m · F cmm. Explore them all at symmetryengine.space/patterns</p>'''
d = os.path.join(OUT, 'worksheet'); os.makedirs(d, exist_ok=True)
open(os.path.join(d, 'index.html'), 'w').write(page('Name the pattern: printable symmetry worksheet | Symmetry Engine',
    'A free printable worksheet: identify six wallpaper symmetry groups by their mirrors, turns and glides.', body, DRAW_JS + "\nrenderTiles();", '/patterns/worksheet/'))
# sitemap fragment
urls = ['/patterns/', '/patterns/worksheet/'] + [f'/patterns/wallpaper/{g}/' for g in ids] + [f'/patterns/frieze/{s}/' for s in fids]
open(os.path.join(OUT, 'sitemap-patterns.txt'), 'w').write('\n'.join('https://symmetryengine.space' + u for u in urls) + '\n')
print('pages', len(urls))
