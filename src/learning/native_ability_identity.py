"""Catalogue-backed nonproduction identities in native human replay commands."""

from src.learning.tournament_commands import ability_matches


def native_ability_matches(action, event, catalog, replay_names, unit_types=None):
    """Extend strict matching with native button and basic-command family names.

    This proves ability semantics only. Callers still need mutually unique native
    timing, targets, queue flags, own actors and regular human flags. A reader
    name alone never establishes a quiet interval or an unknown ability identity.
    """
    if ability_matches(action, event, catalog, replay_names, unit_types):
        return True
    original = event["m_abil"]
    native = catalog.get(action["ability"])
    if original is None or native is None:
        return False
    name = replay_names.get((original["m_abilLink"], original["m_abilCmdIndex"]))
    friendly = native.get("friendly_name", "")
    if (
        not name
        or original["m_abilCmdIndex"] != native.get("link_index")
        or friendly.startswith(("Build ", "Train ", "Research ", "Morph "))
    ):
        return False

    def normalize(text):
        return text.replace(" ", "").lower()

    button_matches = normalize(name) == normalize(native.get("button_name", ""))
    basic_family = name in ("Attack", "Move", "Stop", "HoldPosition", "Patrol")
    return button_matches or (basic_family and friendly.split(" ")[0] == name)
