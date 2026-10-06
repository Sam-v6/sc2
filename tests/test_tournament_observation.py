import unittest

import numpy as np

from src.learning.gameplay import PlayerView
from src.learning.tournament_record import decode_record
from tests.test_tournament_record import record


class TournamentObservationTests(unittest.TestCase):
    def adapt(self, data, index, view, upgrades=()):
        from src.learning.tournament_observation import partial_observation

        return partial_observation(data, index, (176, 184), view, upgrades)

    def test_snapshot_and_hidden_enemy_dynamic_fields_do_not_leak(self):
        data = decode_record(record())
        fields = data["units"]["fields"]
        fields = {k: np.repeat(v, 3, axis=0) for k, v in fields.items()}
        fields["observation"][:] = [1, 2, 3]
        fields["health"][:] = [100, 777, np.nan]
        fields["energy"][:] = [25, 888, 1000]
        data["units"] = {"fields": fields, "step": np.array([0, 1, 1])}
        view = PlayerView()
        first = self.adapt(data, 0, view, [15])
        second = self.adapt(data, 1, view, [15])
        self.assertEqual(first["units"][0]["health"], 100)
        self.assertEqual(second["units"], [])
        self.assertEqual(len(second["memory"]), 1)
        self.assertNotIn("health", second["memory"][0])
        self.assertNotIn("energy", second["memory"][0])
        self.assertEqual(second["memory"][0]["last_seen_loop"], 12)
        self.assertEqual(second["upgrades"], [15])
        self.assertEqual(second["map_size"], [176, 184])

    def test_missing_fields_and_coarse_grids_are_explicit_and_encoder_rejects_them(
        self,
    ):
        from src.learning.entity_examples import state_inputs

        state = self.adapt(decode_record(record()), 0, PlayerView())
        self.assertNotIn("food_used", state["player"])
        self.assertIn("food_used", state["unknown_fields"]["player"])
        self.assertIn("effects", state["unknown_fields"]["world"])
        self.assertEqual(state["map"]["visibility"]["width"], 128)
        self.assertEqual(
            state["map"]["visibility"]["coordinate_system"], "feature_minimap"
        )
        with self.assertRaisesRegex(ValueError, "missing-field"):
            state_inputs(state, 1970, 3801, 296)

    def test_blip_keeps_only_contact_position(self):
        data = decode_record(record())
        data["units"]["fields"]["is_blip"] = np.array([1], dtype=np.int8)
        data["units"]["fields"]["observation"] = np.array([1], dtype=np.uint8)
        state = self.adapt(data, 0, PlayerView())
        self.assertEqual(state["units"], [])
        self.assertEqual(state["memory"], [])
        self.assertEqual(state["radar_contacts"], [{"position": [11.5, 20.25, 8.0]}])

    def test_converter_energy_capacity_is_not_exposed_as_current_energy(self):
        data = decode_record(record())
        data["units"]["fields"]["observation"] = np.array([1], dtype=np.uint8)
        data["units"]["fields"]["energy"] = np.array([200], dtype=np.float32)
        data["units"]["fields"]["energy_max"] = np.array([200], dtype=np.float32)
        state = self.adapt(data, 0, PlayerView())
        self.assertNotIn("energy", state["units"][0])
        self.assertEqual(state["units"][0]["energy_max"], 200)
        self.assertIn("energy", state["unknown_fields"]["units"])

    def test_causal_own_deaths_remove_last_seen_actor_memory(self):
        from src.learning.tournament_observation import partial_observation

        data = decode_record(record())
        fields = data["units"]["fields"]
        fields["alliance"] = np.ones_like(fields["alliance"])
        fields["observation"] = np.ones_like(fields["observation"])
        view = PlayerView()
        first = partial_observation(data, 0, (176, 184), view, [])
        tag = first["units"][0]["tag"]
        second = partial_observation(data, 1, (176, 184), view, [], [tag])
        self.assertEqual(second["owned_memory"], [])
        self.assertNotIn(tag, view.owned)
