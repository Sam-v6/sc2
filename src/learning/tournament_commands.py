"""Reconcile original human commands with converted raw actions, without guessing.

This establishes command identity only. Observation chronology and corpus
eligibility are separate checks performed by the professional importer.
"""

from collections import Counter, defaultdict

from src.learning.gameplay import Command


# Independently named replay flags: user, queue, smart click, minimap, repeat.
# Autocast set/on semantics and unknown bits are not raw toggle equivalents.
REGULAR_FLAGS = 0x100 | 0x2 | 0x8 | 0x10000 | 0x20000


def ability_matches(action, event, catalog, replay_names):
    native = catalog.get(action["ability"])
    if native is None:
        return False
    original = event["m_abil"]
    if original is None:
        return action["ability"] == 1 and native.get("friendly_name") == "Smart"
    key = (original["m_abilLink"], original["m_abilCmdIndex"])
    name = replay_names.get(key)
    return (
        bool(name)
        and name.replace(" ", "").lower()
        == native.get("friendly_name", "").replace(" ", "").lower()
        and original["m_abilCmdIndex"] == native.get("link_index")
    )


def target_matches(action, event):
    data = event["m_data"]
    if "None" in data:
        return action["target_type"] == 0
    if "TargetPoint" in data:
        return action["target_type"] == 2 and action["target"] == [
            int(data["TargetPoint"][axis] / 4096) for axis in ("x", "y")
        ]
    if "TargetUnit" in data:
        return (
            action["target_type"] == 1
            and action["target"] & 0xFFFFFFFF == data["TargetUnit"]["m_tag"]
        )
    return False


def reconcile_commands(events, observations, selections, catalog, replay_names):
    """Require mutual uniqueness, independent ability names/index and selection.

    Selection keys are (original loop, sequence), using original 32-bit tags.
    Converted commands retain full native 64-bit tags. Unknown selections are
    represented by None; a missing selection is also unknown.
    """
    by_loop = defaultdict(list)
    for i, row in enumerate(observations):
        for j, action in enumerate(row["actions"]):
            by_loop[row["loop"]].append(((i, j), action))
    candidates, reasons = [], []
    for event in events:
        key = (event["_gameloop"], event["m_sequence"])
        selected = selections.get(key)
        flags = event["m_cmdFlags"]
        original = event["m_abil"]
        unknown_name = original is not None and not replay_names.get(
            (original["m_abilLink"], original["m_abilCmdIndex"])
        )
        reason = "Unknown replay ability name" if unknown_name else None
        if selected is None:
            reason = "Unknown human selection"
        elif flags & ~REGULAR_FLAGS or not flags & 0x100:
            reason = "Unsupported human command flags"
        matches = []
        selected = None if selected is None else set(selected)
        # Ineligible events still reserve possible identities. The wire format
        # cannot distinguish unsupported flags, or rule out unknown selections.
        for identity, action in by_loop[event["_gameloop"]]:
            actors = [tag & 0xFFFFFFFF for tag in action["tags"]]
            if (
                actors
                and len(set(actors)) == len(actors)
                and (selected is None or set(actors) <= selected)
                and (
                    ability_matches(action, event, catalog, replay_names)
                    or (
                        unknown_name
                        and original["m_abilCmdIndex"]
                        == catalog.get(action["ability"], {}).get("link_index")
                    )
                )
                and target_matches(action, event)
            ):
                matches.append((identity, action))
        candidates.append(matches)
        reasons.append(reason)
    usage = Counter(identity for matches in candidates for identity, _ in matches)
    accepted, unresolved = [], []
    for event, matches, reason in zip(events, candidates, reasons, strict=True):
        if reason is not None or len(matches) != 1 or usage[matches[0][0]] != 1:
            unresolved.append(
                dict(
                    event=event,
                    candidate_count=len(matches),
                    reason=reason or "No mutually unique verified command",
                )
            )
            continue
        identity, action = matches[0]
        target = event["m_data"]
        point = (
            tuple(target["TargetPoint"][axis] / 4096 for axis in ("x", "y"))
            if "TargetPoint" in target
            else None
        )
        command = Command(
            action["ability"],
            tuple(action["tags"]),
            target_unit=action["target"] if action["target_type"] == 1 else None,
            target_point=point,
            queue=bool(event["m_cmdFlags"] & 2),
        )
        command.to_proto()
        accepted.append(
            dict(
                loop=event["_gameloop"],
                sequence=event["m_sequence"],
                command=command,
                converted_position=identity,
            )
        )
    return accepted, dict(
        issued_events=len(events),
        matched_issued_commands=len(accepted),
        unresolved_events=unresolved,
        training_eligible=False,
    )
