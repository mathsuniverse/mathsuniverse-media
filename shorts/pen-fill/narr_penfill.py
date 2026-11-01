import voice
S=[{"text":"One shape. Start with a single tile, and keep going.","gap":0.4},
 {"text":"Every tile is the same hat. The pink ones are just flipped over.","gap":0.35},
 {"text":"It covers the whole floor, with no gaps and no overlaps. But the pattern never repeats, however far you go.","gap":0.35},
 {"text":"Count them. For every flipped hat, there are about six point eight five normal ones: the golden ratio, to the fourth power.","gap":0.35},
 {"text":"It was found in 2023 by David Smith, an amateur from Yorkshire.","gap":0.35},
 {"text":"So why can it never repeat?"}]
for x in voice.narrate(S,'../build/penfill'): print(round(x['start'],2),round(x['end'],2),x['text'][:50])
