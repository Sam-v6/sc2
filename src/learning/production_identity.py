"""Candidate raw abilities from independently named producer metadata."""


def producer_ability(unit_name, command_index, catalog):
    """Return a candidate only; original command reconciliation is still required.

    Replay-reader numeric unit IDs are a different vocabulary from raw engine IDs.
    Require exact unique unit names and matching producer command indexes instead.
    """
    units = [u for u in catalog["units"] if unit_name and u.get("name") == unit_name]
    if len(units) != 1 or "ability_id" not in units[0]:
        return None
    abilities = [
        a for a in catalog["abilities"] if a["ability_id"] == units[0]["ability_id"]
    ]
    if len(abilities) != 1 or abilities[0].get("link_index") != command_index:
        return None
    return abilities[0]["ability_id"]
