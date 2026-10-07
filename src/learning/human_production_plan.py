"""Compile issued human production commands, preserving actor and event identity."""

import math

from src.learning.production_execution import canonical


def compile_commands(accepted, events, data, own_at_loop, metadata_mappings):
    abilities = {a['ability_id']: a for a in data['abilities']}
    units = {u['unit_id']: u for u in data['units']}
    metadata = {}
    for row in metadata_mappings:
        metadata.setdefault((row['link'], row['index']), set()).add(row['native_specific'])
    tickets, unresolved = [], []
    for row in sorted(accepted, key=lambda r: (r['loop'], r['sequence'])):
        command = row['command']
        ability = command['ability']
        friendly = abilities.get(ability, {}).get('friendly_name', '')
        own = own_at_loop.get(row['loop'], {})
        actors = [own.get(tag) for tag in command['units']]
        if friendly.startswith('Cancel'):
            if not all(actor and 8 in units[actor['unit_type']].get('attributes', [])
                       for actor in actors):
                continue  # Combat cancellation is not production work.
        elif not friendly.startswith(('Build ', 'Train ', 'Research ', 'Lift', 'Land')):
            if friendly not in ('Morph OrbitalCommand', 'Morph PlanetaryFortress'):
                continue
        key = (row['loop'], row['sequence'])
        event = events.get(key)
        if not event or not actors or any(actor is None for actor in actors):
            unresolved.append(dict(loop=key[0], sequence=key[1], reason='missing_source_actor_or_event'))
            continue
        raw_ability = event.get('m_abil')
        candidates = []
        if raw_ability:
            source_key = (raw_ability['m_abilLink'], raw_ability['m_abilCmdIndex'])
            candidates = [a for a in metadata.get(source_key, ())
                          if canonical(a, abilities) == canonical(ability, abilities)]
        if not candidates:
            candidates = [a for a, descriptor in abilities.items()
                          if canonical(a, abilities) == canonical(ability, abilities)
                          and descriptor.get('available') is not False
                          and raw_ability
                          and descriptor.get('link_index') == raw_ability['m_abilCmdIndex']]
            if ability in (3678, 3679, 3682, 3683):
                parents = {units[actor['unit_type']]['name'].removesuffix('Flying')
                           for actor in actors}
                candidates = [a for a in candidates if all(
                    abilities[a].get('friendly_name', '').endswith(' ' + parent)
                    for parent in parents)]
        if ability not in (3678, 3679, 3682, 3683, 3700, 3701):
            candidates = [ability]
        if len(candidates) != 1:
            unresolved.append(dict(loop=key[0], sequence=key[1], ability=ability,
                                   reason='ambiguous_specific_ability', candidates=sorted(candidates)))
            continue
        native_command = dict(command, ability=candidates[0],
                              queue=bool(event['m_cmdFlags'] & 2))
        if command.get('target_point') is not None:
            point = event.get('m_data', {}).get('TargetPoint')
            precise = [point[axis] / 4096 for axis in ('x', 'y')] if point else None
            if precise is None or [int(v) for v in precise] != [int(v) for v in command['target_point']]:
                unresolved.append(dict(loop=key[0], sequence=key[1],
                                       reason='source_point_conversion_mismatch'))
                continue
            native_command['target_point'] = precise
        tickets.append(dict(loop=key[0], sequence=key[1],
                            command=native_command,
                            imported_ability=ability, name=abilities[candidates[0]].get('friendly_name'),
                            actor_types=[actor['unit_type'] for actor in actors],
                            original_flags=event['m_cmdFlags']))
    return dict(tickets=tickets, unresolved=unresolved)


def compile_builder_moves(accepted, events, tickets, own_at_loop, neutral_positions):
    """Label actual SCV movements near the same worker's next building site."""
    moves = []
    for row in accepted:
        command = row['command']
        if command['ability'] not in (1, 16) or command.get('target_point') is None or len(command['units']) != 1:
            continue
        actor = own_at_loop.get(row['loop'], {}).get(command['units'][0])
        if actor is None or actor['unit_type'] != 45:
            continue
        key = (row['loop'], row['sequence'])
        next_build = next((t for t in tickets if (t['loop'], t['sequence']) > key
                           and t['actor_types'] == [45]
                           and t['command']['units'] == command['units']
                           and t['name'].startswith('Build ')), None)
        if next_build is None:
            continue
        target = next_build['command'].get('target_point') or neutral_positions.get(next_build['command'].get('target_unit'))
        if target is None or math.dist(target, command['target_point']) >= 6:
            continue
        event = events[key]
        point = event.get('m_data', {}).get('TargetPoint')
        precise = [point[axis]/4096 for axis in ('x', 'y')] if point else None
        if precise != command['target_point']:
            raise ValueError('Builder movement differs from original precise point')
        moves.append(dict(loop=key[0], sequence=key[1], name='Move builder',
                          command=dict(command, queue=bool(event['m_cmdFlags'] & 2)),
                          actor_types=[45], imported_ability=command['ability'],
                          original_flags=event['m_cmdFlags'],
                          source_build=dict(loop=next_build['loop'], sequence=next_build['sequence']),
                          evidence_is_label_only=True))
    return moves
