"""Causal inputs and label-only next human production commitment ordering."""

from scipy.sparse import csr_matrix, hstack, vstack


def next_commitments(events, loop, horizon):
    first = {}
    for time, sequence, family in events:
        if loop <= time < loop + horizon:
            key = (time, sequence)
            first[family] = min(first.get(family, key), key)
    return first


def precedence_target(first, left, right):
    """A known absent commitment follows a present one; two absent/tied are unknown."""
    a, b = first.get(left), first.get(right)
    if a is None and b is None:
        return None
    if a is None:
        return 0
    if b is None:
        return 1
    return None if a[0] == b[0] else int(a < b)


def pair_features(state, family_count, pairs):
    """Repeat one causal state with explicit left/right family identities."""
    identities = csr_matrix(([1] * (2 * len(pairs)),
        ([i for i in range(len(pairs)) for _ in range(2)],
         [j for left, right in pairs for j in (left, family_count + right)])),
        shape=(len(pairs), 2 * family_count))
    return hstack([vstack([state] * len(pairs)), identities]).tocsr()
