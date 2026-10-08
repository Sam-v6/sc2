"""Learn construction locations from map geometry rather than coordinate extrapolation."""

import base64
import numpy as np
from src.learning.global_imitation import coordinate_signs


def decode_terrain(images):
    arrays = {}
    for name, image in images.items():
        values = np.frombuffer(base64.b64decode(image["data"]), dtype=np.uint8)
        if image["bits_per_pixel"] == 1:
            values = np.unpackbits(values)
        arrays[name] = values[: image["width"] * image["height"]].reshape(
            image["height"], image["width"]
        )
    return arrays


def spatial_candidates(size, footprint, spacing=4):
    offset = footprint % 1
    x, y = np.meshgrid(
        np.arange(offset, size[0], spacing), np.arange(offset, size[1], spacing)
    )
    return np.column_stack((x.ravel(), y.ravel()))


def candidate_features(
    state, group, origin, context, points, terrain, footprint, structure_types
):
    signs = coordinate_signs(state, origin)
    actor = np.asarray([u["position"][:2] for u in group]).mean(axis=0)
    columns = [
        (points - origin) * signs / 128.0,
        (points - actor) * signs / 128.0,
        np.linalg.norm(points - actor, axis=1)[:, None] / 128.0,
        np.full((len(points), 1), footprint / 4.0),
    ]
    height, width = terrain["terrain_height"].shape
    pixel = np.clip(points.astype(int), [0, 0], [width - 1, height - 1])
    origin_pixel = np.clip(
        np.asarray(origin).astype(int), [0, 0], [width - 1, height - 1]
    )
    for name in ("placement_grid", "pathing_grid", "terrain_height"):
        grid = terrain[name]
        samples = []
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                shifted = np.clip(pixel + [dx, dy], [0, 0], [width - 1, height - 1])
                samples.append(grid[shifted[:, 1], shifted[:, 0]])
        patch = np.stack(samples, axis=1)
        scale = 255.0 if name == "terrain_height" else 1.0
        columns.append(
            np.column_stack((grid[pixel[:, 1], pixel[:, 0]], patch.mean(axis=1)))
            / scale
        )
    columns.append(
        (
            (
                terrain["terrain_height"][pixel[:, 1], pixel[:, 0]].astype(float)
                - terrain["terrain_height"][origin_pixel[1], origin_pixel[0]]
            )
            / 255.0
        )[:, None]
    )
    # Neutral resources are taken only from currently visible player observations.
    pools = [
        [
            u
            for u in state["units"]
            if u["alliance"] == 3 and u.get("mineral_contents", 0) > 0
        ],
        [
            u
            for u in state["units"]
            if u["alliance"] == 3 and u.get("vespene_contents", 0) > 0
        ],
        [
            u
            for u in state["units"]
            if u["alliance"] == 1 and u["unit_type"] in structure_types
        ],
        [
            u
            for u in state["units"]
            if u["alliance"] == 1 and u["unit_type"] in (18, 36, 130, 132, 134)
        ],
        [u for u in state["units"] if u["alliance"] == 1 and u["unit_type"] == 45],
        [u for u in state["units"] if u["alliance"] == 4],
    ]
    for pool in pools:
        if pool:
            positions = np.asarray([u["position"][:2] for u in pool])
            distances = np.linalg.norm(
                points[:, None, :] - positions[None, :, :], axis=2
            )
            columns.append(
                np.column_stack(
                    (
                        np.minimum(distances.min(axis=1), 128.0) / 128.0,
                        np.exp(-distances / 8.0).sum(axis=1) / 10.0,
                        (distances < 8.0).sum(axis=1) / 10.0,
                    )
                )
            )
        else:
            columns.append(np.tile([1.0, 0.0, 0.0], (len(points), 1)))
    columns.append(np.broadcast_to(context, (len(points), len(context))))
    return np.concatenate(columns, axis=1).astype(np.float32)


def rank_points(policy, features, points):
    logits = policy.predict(features)["ability"]
    order = np.argsort(-(logits[:, 1] - logits[:, 0]), kind="stable")
    return [tuple(p) for p in points[order]]
