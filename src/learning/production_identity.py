"""Candidate raw abilities from independently named producer metadata."""


def producer_ability(unit_name, command_index, catalog):
    """Return a candidate only; original command reconciliation is still required.

    Replay-reader numeric unit IDs are a different vocabulary from raw engine IDs.
    Require exact unique unit names and matching producer command indexes instead.
    """
    unit_name = "VikingFighter" if unit_name == "Viking" else unit_name
    units = [u for u in catalog["units"] if unit_name and u.get("name") == unit_name]
    if len(units) != 1 or "ability_id" not in units[0]:
        return None
    abilities = [
        a for a in catalog["abilities"] if a["ability_id"] == units[0]["ability_id"]
    ]
    if len(abilities) != 1 or abilities[0].get("link_index") != command_index:
        return None
    return abilities[0]["ability_id"]


def research_ability(replay_name, command_index, catalog):
    """Use independently named upgrade metadata before generic API remapping."""
    if replay_name.startswith('Research'):
        name = replay_name.removeprefix('Research').replace(' ', '')
    elif replay_name in ('UpgradeVehicleWeapons1', 'UpgradeVehicleWeapons2', 'UpgradeVehicleWeapons3'):
        name = 'TerranVehicleWeaponsLevel' + replay_name[-1]
    else:
        return None
    upgrades = [u for u in catalog['upgrades'] if u['name'] == name]
    if len(upgrades) != 1:
        return None
    referenced = [a for a in catalog['abilities'] if a['ability_id'] == upgrades[0]['ability_id']]
    if len(referenced) != 1:
        return None
    friendly = referenced[0].get('friendly_name')
    abilities = [a for a in catalog['abilities']
                 if (a['ability_id'] == referenced[0]['ability_id']
                     or (friendly and a.get('friendly_name') == friendly))
                 and a.get('link_index') == command_index and a.get('available') is not False]
    return abilities[0]['ability_id'] if len(abilities) == 1 else None
