"""Protocol unit identities and coarse observed map state, without hidden units."""
import numpy as np
from sc2.ids.unit_typeid import UnitTypeId

TYPE_IDS = list(UnitTypeId)
TYPE_INDEX = {kind: index for index, kind in enumerate(TYPE_IDS)}
CHANNELS = {'count': 40, 'health': 1000, 'shields': 1000,
            'ground_dps': 200, 'air_dps': 200, 'flying': 40,
            'structures': 40, 'detectors': 10, 'cloaked': 10,
            'snapshots': 40, 'visible': 40}
FEATURES = [f'{side}_type_{kind.name}' for side in ('own', 'enemy') for kind in TYPE_IDS]
FEATURES += [f'{side}_cell_{y}_{x}_{channel}' for side in ('own', 'enemy')
             for y in range(8) for x in range(8) for channel in CHANNELS]
GRID_SCALES = np.array(list(CHANNELS.values()), dtype=float)


def observe_units(own, enemy, bounds):
    types = np.zeros((2, len(TYPE_IDS)))
    grid = np.zeros((2, 8, 8, len(CHANNELS)))
    for side, units in enumerate((own, enemy)):
        for unit in units:
            types[side, TYPE_INDEX[unit.type_id]] += 1
            x = min(7, max(0, int((unit.position.x - bounds.x) * 8 / bounds.width)))
            y = min(7, max(0, int((unit.position.y - bounds.y) * 8 / bounds.height)))
            grid[side, y, x] += (1, unit.health, unit.shield, unit.ground_dps,
                unit.air_dps, unit.is_flying, unit.is_structure, unit.detect_range > 0,
                unit.is_cloaked, unit.is_snapshot, unit.is_visible)
    return np.clip(np.concatenate((types.ravel() / 40,
                                  (grid / GRID_SCALES).ravel())), 0, 2)
