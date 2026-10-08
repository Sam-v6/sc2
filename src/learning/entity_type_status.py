"""Current own-unit status by native type, with explicit availability."""

import numpy as np


def unit_type_status(inputs, unit_count):
    raw, types = inputs["encoder"][:2]
    masks = raw[:, 94:124] if raw.shape[1] == 188 else np.ones_like(raw[:, :30])
    base = np.where(masks, raw[:, :30], 0)
    own = base[:, 2] > 0
    observed = own & (base[:, 5] > 0)
    counts = np.bincount(types[observed], minlength=unit_count)
    result = np.zeros((unit_count, 10))
    result[:, 0] = np.log1p(counts) / 5
    result[:, 1] = (
        np.log1p(np.bincount(types[own & ~observed], minlength=unit_count)) / 5
    )
    for column, field in ((2, 11), (4, 19), (6, 20)):
        known = observed & (masks[:, field] > 0)
        denominator = np.bincount(types[known], minlength=unit_count)
        total = np.bincount(
            types[known], weights=base[known, field], minlength=unit_count
        )
        result[:, column] = total / np.maximum(denominator, 1)
        result[:, column + 1] = denominator / np.maximum(counts, 1)
    idle = observed & (masks[:, 19] > 0) & (base[:, 19] == 0)
    unfinished = observed & (masks[:, 11] > 0) & (base[:, 11] < 1)
    result[:, 8] = np.bincount(types[idle], minlength=unit_count) / np.maximum(
        counts, 1
    )
    result[:, 9] = np.bincount(types[unfinished], minlength=unit_count) / np.maximum(
        counts, 1
    )
    return result.ravel().astype(np.float32)
