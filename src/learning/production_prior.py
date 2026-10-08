"""Frozen human-derived family precedence; no authored production priorities."""
from itertools import combinations


def prior_scores(prior, candidates):
    names = prior['names']
    pairs, unsupported = {}, 0
    for a, b in combinations(candidates, 2):
        i, j = names.index(a), names.index(b)
        weights = prior['teacher_prior'].get(f'{min(i,j)},{max(i,j)}', [0, 0])
        total = sum(weights)
        probability = weights[1]/total if total else .5
        if not total:
            unsupported += 1
        pairs[a, b] = probability if i < j else 1-probability
        pairs[b, a] = 1-pairs[a, b]
    scores = {a: sum(pairs[a, b] for b in candidates if b != a)/max(1, len(candidates)-1)
              for a in candidates}
    cycles = sum((pairs[a, b] > .5 and pairs[b, c] > .5 and pairs[c, a] > .5) or
                 (pairs[b, a] > .5 and pairs[c, b] > .5 and pairs[a, c] > .5)
                 for a, b, c in combinations(candidates, 3))
    return scores, unsupported, cycles
