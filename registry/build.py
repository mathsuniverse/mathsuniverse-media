import json
# status: ready = new VIP recipe live + teaser; vip = /vip page exists, older build; premium = paid page under another name; none = no paid landing page found
R=[
# name, domain, pillar, status, paid path, current price, link it for (videos/topics), applications
("Plico Lab","plicolab.space","Maths","ready","/vip/","$9.99","Cube nets, folding, paper/origami puzzles, 11+ non-verbal reasoning","Spatial reasoning practice, 11+ prep, printable worksheets"),
("Interactive Art","interactiveart.space","Maths/Art","ready","/vip/","$199","Gears, spirograph, Tusi couple, ladder/astroid, rolling circles, coffee-cup caustic, maths art","Generative art, 4K exports, design"),
("Interactive Maths","interactivemaths.space","Maths","ready","/vip/","$9.99","Probability (Galileo dice), number puzzles, visual proofs","Classroom maths, probability, problem solving"),
("Fractal Chaos","fractalchaos.space","Maths","ready","/vip/","$9.99","Chaos game, Sierpinski, Mandelbrot, Julia sets, fractals in nature","Chaos theory, iteration, fractal art"),
("Symmetry Engine","symmetryengine.space","Maths","ready","/vip/","$8.99 (should be $9.99)","Escher circle limit, tilings, kaleidoscopes, mirror symmetry, wallpaper groups","Symmetry in art, crystals, design"),
("General Relativity Explorer","generalrelativityexplorer.com","Physics","vip","/vip/","not shown","Gravity, black holes, spacetime, gravitational waves","Physics students, GPS time correction"),
("Human Body Galaxy","humanbodygalaxy.com","Bio","vip","/vip/","not shown","Superhuman series: brain, lungs, heart, anatomy","Biology/anatomy study, revision"),
("Satellite Web","satelliteweb.space","Astronomy","vip","/vip/","$19.99","Satellites, orbits, Starlink, space debris","Orbital mechanics, communications"),
("Voyagers in Space","voyagersin.space","Astronomy","vip","/vip/","not shown","Space missions, Voyager, probes","Space history, mission planning"),
("Cipher Explorer","cipherexplorer.app","CS","vip","/vip (in-app)","$9.99","Codes, ciphers, Enigma, cryptography puzzles","Cryptography, puzzles, security basics"),
("Civilisation Atlas","civilisationatlas.com","History","premium","/premium","$79 / $199","Empires, historical maps, timelines","History lessons, geography"),
("Cyber Explorer","cyberexplorer.space","CS","premium","/premium","$19.99","Hacking, cyber attacks, passwords","Security training, SOC skills"),
("Genome Explorer","genomeexplorer.space","Bio","premium","/premium","$29.99","DNA, CRISPR, genetics, inheritance","Genetics study, biotech"),
("Interactive Exoplanet","interactiveexoplanet.space","Astronomy","premium","/premium","$9.99","Exoplanets, habitable worlds, JWST news","Astronomy, planet science"),
("Interactive Mind","interactivemind.space","Mind","premium","/premium","not shown","Cognitive biases, System 1 vs 2, illusions of the mind","Psychology, decision making"),
("Invention Engine","inventionengine.space","Engineering","premium","/pricing","$99.99 / $199.99","Inventions, trebuchet and Big Questions builds, history of machines","Engineering history, design"),
("Language Explorer","languageexplorer.space","Language","premium","/premium","$49","Word origins, etymology","Languages, writing"),
("Medical Frontier","medicalfrontier.space","Bio","premium","/pricing","$49.99 / $99.99","Medical breakthroughs, vaccines, surgery history","Medicine, health science"),
("Molecular World","molecularworld.space","Chemistry","premium","/premium","$99","Molecules, reactions, chemistry Shorts","Chemistry study"),
("Neural Map","neuralmap.space","CS","premium","/premium","not shown","Neural networks, AI, election-prediction pilot","AI/ML learning"),
("Orthos Lab","orthoslab.space","Mind","premium","/premium","$9.99","3D spatial puzzles, rotation tests","Brain training, spatial IQ"),
("Particle Physics","particlephysics.space","Physics","premium","/premium","$7.99","Standard Model, quarks, CERN","Particle physics"),
("Shape Puzzle","shapepuzzle.space","Maths","premium","/premium","$9.99","Tangrams, shape puzzles, 2-player games (also shapepuzzle.app)","Puzzles, logic"),
("Trade Pulse","tradepulseexplorer.space","Economics","premium","/premium","$149","World trade, shipping, tariffs","Economics, geography"),
("Visual Music","visualmusic.space","Art","premium","/premium","$19.99","Music and maths, harmonics, piano","Music learning"),
("Architectural Wonders","wondersin.space","Engineering","premium","/premium","$79.99","Pyramids, Colosseum, Eiffel Tower, structures","Structural engineering, history"),
("AI Future Sim","aifuturesim.com","CS","none","","","AI history and futures","AI literacy"),
("City Explorer","cityexplorer.space","Society","none","","","Cities, urban growth, architecture over time","Urban planning, geography"),
("Climate Futures","climatefutures.space","Earth","none","","","Climate change, 1850 to 2100","Climate science"),
("Deep Time Explorer","deeptimeexplorer.earth","Earth","none","","","Geological time, dinosaurs, Earth history","Geology, evolution"),
("Echo-N Lab","echonlab.space","Mind","none","","","Working memory, dual n-back","Brain training"),
("Engineering Systems","engineeringsystems.space","Engineering","none","","$19.99 mentioned","How It Works (devices pulled apart), systems","Engineering education"),
("Focus Swarm","focusswarm.space","Mind","none","","","Focus and attention","Concentration training"),
("Interactive Code","interactivecode.space","CS","none","","","Logic gates, coding","Computing basics"),
("Interactive Cosmic Scale","interactivecosmicscale.com","Astronomy","none","","","Scale of the universe, atoms to galaxies","Sense of scale"),
("Interactive Cosmos","interactivecosmos.space","Astronomy","none","","","Stars, galaxies, night sky","Astronomy"),
("Interactive History","interactivehistory.space","History","none","","","World history timeline","History lessons"),
("Interactive Money","interactivemoney.space","Economics","none","","","Money, interest, inflation","Personal finance, economics"),
("Interactive Physics","interactivephysics.space","Physics","none","","","Gravity, free fall, mechanics","Physics lessons"),
("Micro Explorer","microexplorer.space","Bio","none","","","Bacteria, microscope, cells","Microbiology"),
("Ocean Explorer","oceanexplorer.space","Earth","none","","","Ocean zones, deep sea","Marine science"),
("Pattern Pulse","patternbeat.space","Mind","none","","","IQ patterns, sequences","Fluid intelligence"),
("Perspective Point","perspectivepoint.space","Mind","none","","","3D perspective puzzles","Spatial reasoning"),
("Pioneer Explorers","pioneerexplorers.space","History","none","","","Age of exploration, navigators","History, navigation"),
("Quantum Mechanics","quantummechanics.app","Physics","none","","","Quantum, double slit, superposition","Quantum physics"),
("Solar Planet","solarplanet.space","Astronomy","none","","","Planets, solar system","Astronomy for all ages"),
]
keys="name domain pillar status path price link_for applications".split()
data=[dict(zip(keys,r)) for r in R]
for d in data:
    d["paid_url"]=f"https://{d['domain']}{d['path']}" if d["path"] and "in-app" not in d["path"] else (f"https://{d['domain']}/vip" if d["path"] else "")
json.dump(data,open("explorers.json","w"),indent=1)
from collections import Counter; print(len(data),Counter(d["status"] for d in data))
