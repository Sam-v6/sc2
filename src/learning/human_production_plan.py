"""Compile issued human production commands, preserving actor and event identity."""

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
