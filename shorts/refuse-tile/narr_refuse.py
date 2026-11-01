import voice
S=[{"text":"Five shapes that refuse to tile your floor.","gap":0.3},
 {"text":"Number five: circles. Pack them as tight as you like, and about nine percent of the floor stays bare.","gap":0.35},
 {"text":"Number four: the pentagon. Three corners make three hundred and twenty-four degrees. That leaves a thirty-six degree gap. Every single time.","gap":0.35},
 {"text":"Number three: the octagon. Two corners leave a square hole, so you have to cheat and add squares.","gap":0.35},
 {"text":"Number two: Penrose's kite and dart. They cover the floor forever, but the pattern never repeats.","gap":0.35},
 {"text":"And number one: the hat. One single tile, found in 2023 by an amateur called David Smith. It covers the whole floor, and it never, ever repeats."}]
for x in voice.narrate(S,'../build/refuse'): print(round(x['start'],2),round(x['end'],2),x['text'][:50])
