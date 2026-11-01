import voice
S=[{"text":"One shape. Start with a single tile, and keep going.","gap":0.4},
 {"text":"Every tile is the same hat. The gold ones are just flipped over.","gap":0.35},
 {"text":"It covers the whole floor, with no gaps and no overlaps. But the pattern never repeats, however far you go.","gap":0.35},
 {"text":"Count them. For every flipped hat, there are about six point eight five normal ones: the golden ratio, to the fourth power.","gap":0.35},
 {"text":"It was found in 2023 by David Smith, an amateur from Yorkshire.","gap":0.5},
 {"text":"But look closer. The hats secretly team up into clusters, and every gold hat sits in a cluster of four.","gap":0.4},
 {"text":"The clusters team up again. Four hats, then twenty five, then one hundred and sixty nine, then one thousand one hundred and fifty six.","gap":0.4},
 {"text":"Two squared, five squared, thirteen squared, thirty four squared. Squares of Fibonacci numbers, hiding in the floor.","gap":0.4},
 {"text":"Bigger and bigger copies, forever. That ladder is why it can never repeat.","gap":0.35},
 {"text":"So which other shapes hide a ladder like this?"}]
for x in voice.narrate(S,'../build/penfill'): print(round(x['start'],2),round(x['end'],2),x['text'][:50])
