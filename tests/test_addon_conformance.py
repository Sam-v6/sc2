import unittest
from copy import deepcopy
from src.learning.addon_conformance import in_place_addon_label


class AddonConformanceTests(unittest.TestCase):
    def fixture(self):
        return dict(
            player=1,
            raw_name="BuildBarracksReactor",
            event=dict(
                _gameloop=100,
                m_sequence=7,
                m_cmdFlags=0x1000100,
                m_abil=dict(m_abilCmdIndex=1),
                m_data=dict(TargetPoint=dict(x=40960, y=81920)),
            ),
            action=dict(ability=3683, tags=[17], target_type=0, target=None),
            actors=[
                dict(
                    tag=17,
                    name="Barracks",
                    alliance=1,
                    position=[10.0, 20.0],
                    is_flying=False,
                    build_progress=1.0,
                )
            ],
            selected=[17],
            starts=[
                dict(
                    _gameloop=100,
                    m_upkeepPlayerId=1,
                    m_unitTypeName=b"BarracksReactor",
                    m_x=12.5,
                    m_y=19.5,
                )
            ],
        )

    def test_preserves_raw_event_and_uses_verified_no_target_execution(self):
        args = self.fixture()
        prior = deepcopy(args)
        result = in_place_addon_label(**args)
        self.assertIsNotNone(result)
        command, proof = result
        self.assertEqual(command.ability, 3683)
        self.assertIsNone(command.target_point)
        self.assertEqual(proof["source_event"], args["event"])
        self.assertEqual(proof["kind"], "observed_in_place_addon_equivalence")
        self.assertEqual(args, prior)

    def test_remote_flying_grouped_missing_or_wrong_effects_remain_unknown(self):
        changes = [
            lambda a: a["actors"][0].update(is_flying=True),
            lambda a: a["actors"][0].update(position=[11.0, 20.0]),
            lambda a: a["actors"].append(dict(a["actors"][0], tag=18)),
            lambda a: a["selected"].append(18),
            lambda a: a["starts"].clear(),
            lambda a: a["starts"][0].update(_gameloop=101),
            lambda a: a["starts"][0].update(m_unitTypeName=b"FactoryReactor"),
            lambda a: a["event"].update(m_cmdFlags=0x1000140),
            lambda a: a["event"]["m_abil"].update(m_abilCmdIndex=0),
        ]
        for change in changes:
            args = self.fixture()
            change(args)
            if len(args["actors"]) > 1:
                args["selected"].append(18)
            # An unrelated selection alone is permitted; an unobserved actor is not.
            if args["selected"] == [17, 18] and len(args["actors"]) == 1:
                args["selected"] = [18]
            self.assertIsNone(in_place_addon_label(**args))
