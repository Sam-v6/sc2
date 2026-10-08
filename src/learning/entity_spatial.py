"""Full-resolution, player-visible grid patches for raw map candidates."""

import numpy as np

from src.learning.spatial_construction import decode_terrain


def spatial_features(
    state, terrain, centers, radii, cell_size=8, source_geometry=False
):
    """Keep every cell pixel; edge padding has an explicit validity mask.

    Grid order is height, pathing, placement, visibility and creep. Coordinates
    stay available separately for cell-conditioned offsets. No destination is
    removed on the basis of visibility, pathing or placement.
    """
    images = {**terrain, **state["map"]}
    grids = decode_terrain(
        {name: image for name, image in images.items() if image.get("known", True)}
    )
    size = np.asarray(state["map_size"], dtype=int)
    names = ("terrain_height", "pathing_grid", "placement_grid", "visibility", "creep")
    resolution, availability = [], []
    for name in names:
        if name not in grids:
            if not source_geometry:
                raise ValueError("Missing spatial grid requires availability inputs")
            grids[name] = np.zeros(tuple(size[::-1]), np.uint8)
            resolution.extend((0, 0))
            availability.append(0)
            continue
        availability.append(1)
        image, grid = images[name], grids[name]
        if image.get("coordinate_system") == "feature_minimap":
            if not source_geometry:
                raise ValueError(
                    "Feature-minimap geometry requires explicit source inputs"
                )
            if (
                image.get("world_size") != list(size)
                or image.get("transform")
                != "world_y_flip_then_uniform_max_dimension_scale"
                or grid.shape[0] != grid.shape[1]
            ):
                raise ValueError("Unverified feature-minimap geometry")
            # Sample each native world tile at its center. The original feature
            # grid flips world y before uniformly scaling by the larger extent.
            scale = grid.shape[1] / max(size)
            x = np.floor((np.arange(size[0]) + 0.5) * scale).astype(int)
            y = np.floor((size[1] - np.arange(size[1]) - 0.5) * scale).astype(int)
            grids[name] = grid[np.ix_(y, x)]
            resolution.extend((1 / scale, 1 / scale))
        else:
            if image.get("coordinate_system") not in (None, "native"):
                raise ValueError("Unknown spatial grid geometry")
            if grid.shape != tuple(size[::-1]):
                raise ValueError("Spatial grid dimensions must match the map")
            resolution.extend((1, 1))
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
    features = np.concatenate(
        (
            np.asarray(centers) / size,
            patches.reshape(len(centers), -1),
            valid.reshape(len(centers), -1),
        ),
        axis=1,
    ).astype(np.float32)

    if source_geometry:
        features = np.concatenate(
            (
                features,
                np.tile(
                    np.asarray(resolution + availability, np.float32), (len(centers), 1)
                ),
            ),
            axis=1,
        )
    return features
