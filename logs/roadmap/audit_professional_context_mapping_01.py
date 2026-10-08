"""Inspect frozen teaching contexts; no fitting or additional predictions."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist

root = Path("logs/roadmap/professional-wider-actor-01")
output = Path("logs/roadmap/professional-context-mapping-01.json")
assert not output.exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
comparison = json.loads((root / "comparison.json").read_text())
assert sha(root / "cache.npz") == comparison["cache_archive_sha256"]
report = json.loads((root / "lbfgs/report.json").read_text())
rows = [r for r in report["commands"] if r["game"] != "774" and r["exclusion"] is None]
with np.load(root / "cache.npz", allow_pickle=False) as archive:
    contexts = archive["contexts"]
assert contexts.shape == (4510, 32) and len(rows) == 4510
assert np.isfinite(contexts).all()
_, inverse, counts = np.unique(contexts, axis=0, return_inverse=True, return_counts=True)
duplicate_groups = []
for group in np.flatnonzero(counts > 1):
    indices = np.flatnonzero(inverse == group)
    duplicate_groups.append([dict(game=rows[i]["game"], row=rows[i]["row"], ability=rows[i]["ability"]) for i in indices])
singular = np.linalg.svd(contexts - contexts.mean(axis=0), compute_uv=False)
abilities = np.array([r["ability"] for r in rows])
nearest = []
for ability in np.unique(abilities):
    indices = np.flatnonzero(abilities == ability)
    if len(indices) < 2:
        continue
    points = contexts[indices]
    distances = cdist(points, points, metric="euclidean")
    np.fill_diagonal(distances, np.inf)
    neighbors = np.argmin(distances, axis=1)
    for local, neighbor in enumerate(neighbors):
        i, j = indices[local], indices[neighbor]
        nearest.append(dict(game=rows[i]["game"], row=rows[i]["row"], ability=int(ability), distance=float(distances[local, neighbor]), neighbor_game=rows[j]["game"], neighbor_row=rows[j]["row"], actor_exact=set(rows[i]["prediction"]["actors"]) == set(rows[i]["gold_actors"])))
distances = np.array([r["distance"] for r in nearest])
receipt = dict(
    cache_sha256=sha(root / "cache.npz"),
    parent_report_sha256=sha(root / "lbfgs/report.json"),
    helper_sha256=sha(Path(__file__)),
    rows=len(rows), unique_contexts=len(counts), duplicate_groups=duplicate_groups,
    centered_singular_values=singular.tolist(),
    centered_numerical_rank=int(np.linalg.matrix_rank(contexts - contexts.mean(axis=0))),
    saturated_fraction=float(np.mean(np.abs(contexts) > .99)),
    nearest_same_ability_quantiles=dict(zip(["min", "p25", "median", "p75", "max"], np.quantile(distances, [0, .25, .5, .75, 1]).tolist())),
    nearest_same_ability=nearest,
    policy_updates=0, native_games=0, rl_updates=0,
    scope="Frozen teaching contexts only. Unique numerical contexts do not establish sufficient observations, causal availability or generalization.",
)
output.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({k:v for k,v in receipt.items() if k not in ("nearest_same_ability", "duplicate_groups")}, indent=2))
print("Duplicate groups:", len(duplicate_groups))
