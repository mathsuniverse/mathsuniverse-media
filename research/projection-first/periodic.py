"""Step 3: sufficient tests for periodic tiling of a shape S (boundary word on unit steps).

  BN      Beauquier-Nivat: S tiles by translations (lattice tiling) iff boundary = A B C A^ B^ C^
          (here: factor points restricted to unit-step vertices; passing is a proof of periodicity).
  Conway  boundary = A B C A^ E F with B, C, E, F centrosymmetric -> isohedral p2 tiling (periodic).
Shapes failing both are NOT shown aperiodic; they are just not caught by these two tests.
"""
import gzip
import json
import sys
from collections import Counter, defaultdict

from shapes import bn_translation, conway


def load(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        return json.load(f)


def classify(word, n2):
    if word is None:
        return "non-simple"
    if bn_translation(word, n2):
        return "BN"
    if len(word) <= 40 and conway(word, n2):
        return "Conway"
    return "not-caught"


if __name__ == "__main__":
    # sanity: SQ control
    assert bn_translation([0, 1, 2, 3], 4)
    assert bn_translation([0, 0, 1, 2, 2, 3], 4)  # domino
    out = {}
    for path in sys.argv[1:]:
        d = load(path)
        n2 = {"AB": 8, "P3": 10, "SQ": 4}[d["system"]]
        kmax_census = 6
        census = defaultdict(Counter)
        survivors = []
        for s in d["shapes"]:
            passed = s.get("Rpass")
            if s["k"] <= kmax_census or passed:
                c = classify(s["word"], n2)
                if s["k"] <= kmax_census:
                    census[s["k"]][c] += 1
                if passed:
                    survivors.append({"id": s["id"], "k": s["k"], "comp": s["comp"], "Rpass": passed,
                                      "Rfail": s.get("Rfail"), "periodic_test": c, "word": s["word"],
                                      "history": s["history"]})
        out[d["system"]] = {"census_k<=6": {k: dict(v) for k, v in sorted(census.items())},
                            "partition_survivors": survivors}
        print(d["system"], json.dumps(out[d["system"]]["census_k<=6"]))
        for s in survivors:
            print("  survivor", s["id"], "k", s["k"], "comp", s["comp"], "Rpass", s["Rpass"], "Rfail",
                  s["Rfail"], s["periodic_test"], s["word"])
    json.dump(out, open("results/periodic.json", "w"), indent=1)
