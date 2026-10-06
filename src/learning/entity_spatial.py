"""Full-resolution, player-visible grid patches for raw map candidates."""

import numpy as np

from src.learning.spatial_construction import decode_terrain


def spatial_features(state, terrain, centers, radii, cell_size=8):
    """Keep every cell pixel; edge padding has an explicit validity mask.

    Grid order is height, pathing, placement, visibility and creep. Coordinates
    stay available separately for cell-conditioned offsets. No destination is
    removed on the basis of visibility, pathing or placement.
    """
    grids = decode_terrain({**terrain, **state["map"]})
    size = np.asarray(state["map_size"], dtype=int)
    names = ("terrain_height", "pathing_grid", "placement_grid", "visibility", "creep")
    if any(grids[name].shape != tuple(size[::-1]) for name in names):
        raise ValueError("Spatial grid dimensions must match the map")
    planes = np.stack(
        [
            grids["terrain_height"] / 255.0,
            grids["pathing_grid"] != 0,
            grids["placement_grid"] != 0,
            grids["visibility"] / 2.0,
            grids["creep"] != 0,
        ],
        axis=-1,
    ).astype(np.float32)
    patches = np.zeros((len(centers), cell_size, cell_size, 5), np.float32)
    valid = np.zeros((len(centers), cell_size, cell_size), np.float32)
    for i, (center, radius) in enumerate(zip(centers, radii, strict=True)):
        start = np.rint(center - radius).astype(int)
        end = np.rint(center + radius).astype(int)
        extent = end - start
        if (
            np.any(start < 0)
            or np.any(end > size)
            or np.any(extent <= 0)
            or np.any(extent > cell_size)
        ):
            raise ValueError("Candidate cell must cover an in-map pixel rectangle")
        x, y = start
        width, height = extent
        patches[i, :height, :width] = planes[y : y + height, x : x + width]
        valid[i, :height, :width] = 1
    return np.concatenate(
        (
            np.asarray(centers) / size,
            patches.reshape(len(centers), -1),
            valid.reshape(len(centers), -1),
        ),
        axis=1,
    ).astype(np.float32)
