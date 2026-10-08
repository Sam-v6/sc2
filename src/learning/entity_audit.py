"""Complete command reconstruction with predicted conditioning and named oracles."""

from collections import Counter

import numpy as np

from src.learning.entity_examples import decode_command


def audit_commands(policy, examples, point_tolerance=1):
    counts = {
        name: Counter()
        for name in ("predicted", "ability_oracle", "ability_actor_oracle")
    }
    exclusions = Counter()
    timed, representable = 0, 0
    distances = {name: [] for name in counts}
    fields = ("ability", "actors", "mode", "queue", "target")
    for inputs, label, command, exclusion in examples:
        if exclusion:
            exclusions[exclusion] += 1
        representable += int(label is not None)
        timing_known = label is not None and label["delay"] is not None
        timed += int(timing_known)
        for name in counts:
            conditioning = {}
            if name != "predicted":
                conditioning["ability"] = command.ability
            if name == "ability_actor_oracle":
                if any(tag not in inputs["tags"] for tag in command.units):
                    continue
                conditioning["actors"] = tuple(
                    inputs["tags"].index(tag) for tag in command.units
                )
            prediction = policy.predict(inputs, **conditioning)
            if prediction is None:
                continue
            actual = decode_command(prediction, inputs)
            same_mode = (
                actual.autocast == command.autocast
                and (actual.target_unit is not None)
                == (command.target_unit is not None)
                and (actual.target_point is not None)
                == (command.target_point is not None)
            )
            same_target = actual.target_unit == command.target_unit
            if command.target_point is not None:
                same_target = False
                if actual.target_point is not None:
                    distance = float(
                        np.linalg.norm(
                            np.asarray(actual.target_point) - command.target_point
                        )
                    )
                    distances[name].append(distance)
                    same_target = distance <= point_tolerance
            matches = dict(
                ability=actual.ability == command.ability,
                actors=set(actual.units) == set(command.units),
                mode=same_mode,
                queue=actual.queue == command.queue,
                target=same_target,
            )
            matches["complete"] = all(matches.values()) and exclusion is None
            same_delay = (
                timing_known and prediction["delay"] == policy.delays[label["delay"]]
            )
            matches["delay"] = bool(same_delay)
            matches["complete_with_timing"] = bool(matches["complete"] and same_delay)
            counts[name].update({k: int(v) for k, v in matches.items()})
    names = (*fields, "complete", "delay", "complete_with_timing")
    return dict(
        commands=len(examples),
        representable=representable,
        timed_commands=timed,
        exclusions=dict(exclusions),
        point_tolerance=point_tolerance,
        **{name: {key: counts[name][key] for key in names} for name in counts},
        point_errors={
            name: dict(
                count=len(values), mean=float(np.mean(values)) if values else None
            )
            for name, values in distances.items()
        },
        scope="Human-state reconstruction; ordinary predictions use predicted ability and actors. Oracles are diagnostics; point matches use stated tile tolerance. No native play evidence.",
    )
