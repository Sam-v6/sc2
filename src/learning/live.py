"""Engine-derived ability inventory and batched availability, without strategy masks."""

from s2clientprotocol import query_pb2 as query, sc2api_pb2 as pb
from src.learning.gameplay import protocol_dict


def ability_query(tags):
    return query.RequestQuery(
        abilities=[query.RequestQueryAvailableAbilities(unit_tag=tag) for tag in tags],
        ignore_resource_requirements=False,
    )


def legal_commands(commands, response):
    """Precheck ability availability; target validity/resource races remain engine checks."""
    available = {
        entry.unit_tag: {ability.ability_id for ability in entry.abilities}
        for entry in response.abilities
    }
    for command in commands:
        command.to_proto()
        if any(
            command.ability not in available.get(tag, set()) for tag in command.units
        ):
            raise ValueError(
                "Command uses a unit or ability not currently available to the player"
            )
    return commands


def ability_catalog(data):
    return [protocol_dict(ability) for ability in data.abilities]


async def issue(server, commands):
    """Preserve command order and independent unit commands in one request."""
    return (
        await server._execute(
            action=pb.RequestAction(
                actions=[command.to_proto() for command in commands]
            )
        )
    ).action
