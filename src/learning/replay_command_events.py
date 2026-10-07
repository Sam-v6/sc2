"""Expand original command-manager repeats with explicit source provenance."""


def command_events(events, user_id):
    commands, unresolved = [], []
    previous = None
    target = None
    for event in events:
        if event.get('_userid', {}).get('m_userId') != user_id:
            continue
        kind = event['_event'].rsplit('.', 1)[-1]
        if kind in ('SSelectionDeltaEvent', 'SControlGroupUpdateEvent'):
            previous, target = None, None
        elif kind == 'SCmdEvent':
            commands.append(event)
            previous, target = event, None
        elif kind in ('SCmdUpdateTargetPointEvent', 'SCmdUpdateTargetUnitEvent'):
            target = event
        elif kind == 'SCommandManagerStateEvent':
            if (previous is None or event.get('m_state') != 1
                    or (target is not None and target['_gameloop'] != event['_gameloop'])):
                unresolved.append(dict(event=event, reason='unverified_repeat_context'))
                target = None
                continue
            data = previous['m_data']
            if target is not None:
                key = 'TargetPoint' if target['_event'].endswith('PointEvent') else 'TargetUnit'
                data = {key: target['m_target']}
            origin = previous.get('source_command', dict(
                loop=previous['_gameloop'], sequence=previous['m_sequence']))
            expanded = dict(previous, _gameloop=event['_gameloop'],
                            m_sequence=event['m_sequence'], m_data=data,
                            source_command=origin, source_manager=event,
                            source_target_update=target)
            commands.append(expanded)
            previous, target = expanded, None
    return commands, unresolved
