"""Five Shorts cut from long video 03 (Symmetry in nature): one per symmetry break.

Each Short re-renders that chapter's scene in the vertical 9:16 frame (same art, same
narration and music from the long video), with a question hook first and an end card
pointing to the Break the symmetry lab and the full video.

    python3 short_breaks.py check            # print spans and durations
    python3 short_breaks.py stills K t...    # PNG stills for break K (4..8) at Short times t
    python3 short_breaks.py render K         # build/breaks/breakK.mp4 (with audio)
"""
import os, sys, json, subprocess
os.environ['MU_FORMAT'] = 'short'
os.environ.setdefault('MU_THEME', 'night')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import video_long03 as L
from mu_style import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'build', 'breaks')
LONG_MP4 = os.path.join(HERE, '..', 'build', 'long03', 'symmetry-long.mp4')
TAIL = 0.6       # let the last word ring
CARD = 5.0       # end card length

# chapter -> (hook line 1, hook line 2, accent, number of leading words to drop)
SPEC = {
    4: ('Why does anything', 'exist at all?', GOLD, 9),      # drop "Break one happened in the first fraction of a second."
    5: ('The universe was', 'almost perfectly smooth', CYAN, 2),   # drop "Break two."
    6: ('Your two hands', 'can never match', PINK, 2),       # drop "Break three."
    7: ('How does a ball of cells', 'grow a head?', GREEN, 2),  # drop "Break four."
    8: ('Why is your heart', 'on the LEFT?', PINK, 0),
}
ART_FROM = {4: ('pairs', 0.8), 7: ('cell', 0.3)}
SCENES = {4: L._scene_4, 5: L._scene_5, 6: L._scene_6, 7: L._scene_7, 8: L._scene_8}


def span(k):
    beats = [b for b in L.BEATS if b['chapter'] and b['chapter'][0] == k]
    words = beats[0]['words']
    drop = SPEC[k][3]
    s0 = words[drop]['start'] - 0.25 if drop else beats[0]['start'] - 0.1
    e0 = beats[-1]['end']
    return s0, e0


def make(k):
    s0, e0 = span(k)
    vo = e0 - s0
    dur = vo + TAIL + CARD
    h1, h2, acc, _ = SPEC[k]
    t_card = vo + TAIL - 0.2

    caps = [(0.0, 3.0, h1, h2, acc)]
    for phrase, l1, l2 in L.CAPTION_CUES:
        x = L.at(phrase)
        if x is None or not (s0 - 3 <= x <= e0):
            continue
        caps.append((max(3.0, x - s0 - 0.15), None, l1, l2, CYAN))
    caps.sort(key=lambda c: c[0])
    # each caption holds until the next one; drop any squeezed to nothing by the hook
    fixed = []
    for i, c in enumerate(caps):
        end = caps[i + 1][0] - 0.12 if i + 1 < len(caps) else t_card - 0.1
        if c[1] is not None:
            end = min(end, c[1])
        if end - c[0] > 0.9:
            fixed.append((c[0], end, c[2], c[3], c[4]))
    fixed.append((t_card, dur + 1, 'Break it yourself:', 'symmetryengine.space/break', GOLD))

    chips = []
    for phrase, name, date in L.CITATIONS:
        x = L.at(phrase)
        if x is not None and s0 - 1 <= x <= e0:
            chips.append((x - s0, min(x - s0 + 4.5, t_card - 0.2), f'{name}, {date}'))

    def draw(t, cr, lc):
        tl = s0 + min(t, vo + TAIL)          # the long video's clock; hold the last frame under the card
        # some scenes only start drawing at a later phrase: start the art there so frame 0 isn't empty
        if k in ART_FROM:
            tl = max(tl, L.tt(ART_FROM[k][0]) + ART_FROM[k][1])
        inn = ramp(t, 0.0, 0.4) * (1 - 0.65 * ramp(t, t_card - 0.3, t_card + 0.5))
        SCENES[k](tl, cr, lc, inn)
        header(cr)
        captions(cr, t, fixed)
        for a, b, s in chips:
            chip(cr, s, window(t, a, b), italic=True)
        if t > t_card:
            chip(cr, 'Full story: Symmetry in nature (link below)', window(t, t_card + 0.4, dur + 1), italic=True)
    return draw, dur, s0, e0


def audio(k, path):
    s0, e0 = span(k)
    vo = e0 - s0 + TAIL
    dur = vo + CARD
    # narration + music from the long video, then the long video's music-only outro under the card
    outro_start = L.VOICE_END + 2.0
    cmd = ['ffmpeg', '-v', 'error', '-y',
           '-ss', f'{s0:.3f}', '-t', f'{vo + 0.6:.3f}', '-i', LONG_MP4,
           '-ss', f'{outro_start:.3f}', '-t', f'{CARD + 1.0:.3f}', '-i', LONG_MP4,
           '-filter_complex',
           f'[0:a]afade=t=in:d=0.15,afade=t=out:st={vo - 0.1:.3f}:d=0.6[a];'
           f'[1:a]afade=t=in:d=0.8,afade=t=out:st={CARD - 1.2:.3f}:d=1.2[b];'
           f'[a][b]acrossfade=d=0.6[m];[m]atrim=0:{dur:.3f},loudnorm=I=-15:TP=-1.5[o]',
           '-map', '[o]', '-ar', '48000', '-ac', '2', path]
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    mode = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    if mode == 'check':
        for k in SPEC:
            d, dur, s0, e0 = make(k)
            print(f'break {k}: long {s0:.1f}-{e0:.1f}  short {dur:.1f}s')
    elif mode == 'stills':
        k = int(sys.argv[2]); d, dur, s0, e0 = make(k)
        sd = os.path.join(OUT, f'stills{k}'); os.makedirs(sd, exist_ok=True)
        for x in sys.argv[3:]:
            t = float(x)
            make_frame(d, t, os.path.join(sd, f't{t:05.1f}.png'))
    elif mode == 'render':
        from render_pipe import render, mux
        k = int(sys.argv[2]); d, dur, s0, e0 = make(k)
        silent = os.path.join(OUT, f'break{k}_v.mp4'); wav = os.path.join(OUT, f'break{k}.wav')
        audio(k, wav)
        render(d, dur, silent, progress_every=300, label=f'b{k} ')
        mux(silent, wav, os.path.join(OUT, f'break{k}.mp4'))
