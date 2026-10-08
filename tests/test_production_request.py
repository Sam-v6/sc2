import unittest

from src.learning.gameplay import Command


class ProductionRequestTests(unittest.TestCase):
    def test_retry_attempts_belong_to_the_request_despite_unrelated_completion(self):
        from src.learning.production_request import ProductionRequest
        request = self.request()
        self.assertEqual(request.attempt, 0)
        for attempt in range(1, 4):
            request = ProductionRequest(request.command, self.state, self.data, retry_of=request)
            other = ProductionRequest(Command(524, (self.worker['tag'],)), self.state, self.data)
            self.assertEqual(other.status(dict(self.state, game_loop=10600,
                             units=[dict(self.worker, orders=[dict(ability_id=524, progress=.1)])])), 'started')
            self.assertEqual(request.attempt, attempt)
            self.assertEqual(other.attempt, 0)

    def setUp(self):
        self.data = dict(
            abilities=[
                dict(ability_id=319, friendly_name="Build SupplyDepot"),
                dict(ability_id=320, friendly_name="Build Refinery"),
                dict(ability_id=524, friendly_name="Train SCV"),
            ],
            units=[dict(unit_id=19, ability_id=319), dict(unit_id=20, ability_id=320)],
        )
        self.worker = dict(
            tag=4348182529, unit_type=45, alliance=1, position=[41.35, 132.75]
        )
        self.state = dict(game_loop=10565, units=[self.worker], action_errors=[])

    def request(self, command=None):
        from src.learning.production_request import ProductionRequest

        return ProductionRequest(
            command or Command(319, (self.worker["tag"],), target_point=(39, 127.5)),
            self.state,
            self.data,
        )

    def test_delayed_native_placement_error_ends_pending_request(self):
        request = self.request()
        later = dict(
            self.state,
            game_loop=10684,
            action_errors=[
                dict(unit_tag=self.worker["tag"], ability_id=319, result=44)
            ],
        )
        self.assertEqual(request.status(later), "failed")

    def test_build_order_and_elapsed_delay_do_not_replace_foundation_evidence(self):
        request = self.request()
        later = dict(
            self.state,
            game_loop=10610,
            units=[
                dict(
                    self.worker,
                    orders=[
                        dict(ability_id=319, target_world_space_pos=dict(x=39, y=128))
                    ],
                )
            ],
        )
        self.assertEqual(request.status(later), "pending")
        later["units"].append(
            dict(
                tag=2, unit_type=19, alliance=1, position=[39, 128], build_progress=0.01
            )
        )
        self.assertEqual(request.status(later), "started")

    def test_existing_structure_cannot_acknowledge_new_request(self):
        self.state["units"].append(
            dict(tag=2, unit_type=19, alliance=1, position=[39, 128])
        )
        request = self.request()
        self.assertEqual(request.status(dict(self.state, game_loop=10573)), "pending")

    def test_refinery_remembers_geyser_position_after_neutral_target_disappears(self):
        self.state["units"].append(
            dict(tag=3, unit_type=342, alliance=3, position=[30, 120])
        )
        request = self.request(Command(320, (self.worker["tag"],), target_unit=3))
        later = dict(
            self.state,
            game_loop=10573,
            units=[
                self.worker,
                dict(
                    tag=4,
                    unit_type=20,
                    alliance=1,
                    position=[30, 120],
                    build_progress=0.01,
                ),
            ],
        )
        self.assertEqual(request.status(later), "started")

    def test_training_order_acknowledges_only_its_owned_actor(self):
        self.state["units"].append(dict(tag=10, unit_type=18, alliance=1))
        request = self.request(Command(524, (10,)))
        unrelated = dict(
            tag=11, unit_type=18, alliance=1, orders=[dict(ability_id=524)]
        )
        later = dict(self.state, game_loop=10573, units=[unrelated])
        self.assertEqual(request.status(later), "actor_missing")
        later["units"].append(dict(unrelated, tag=10))
        self.assertEqual(request.status(later), "started")

    def test_existing_train_order_does_not_acknowledge_new_queued_order(self):
        actor = dict(
            tag=10,
            unit_type=18,
            alliance=1,
            orders=[dict(ability_id=524, progress=0.5)],
        )
        self.state["units"].append(actor)
        request = self.request(Command(524, (10,), queue=True))
        later = dict(self.state, game_loop=10573)
        self.assertEqual(request.status(later), "pending")
        later["units"] = [
            dict(actor, orders=actor["orders"] + [dict(ability_id=524, progress=0)])
        ]
        self.assertEqual(request.status(later), "started")

    def test_queued_order_can_start_when_previous_unit_finishes_between_frames(self):
        actor = dict(
            tag=10,
            unit_type=18,
            alliance=1,
            orders=[dict(ability_id=524, progress=0.99)],
        )
        self.state["units"].append(actor)
        request = self.request(Command(524, (10,), queue=True))
        later = dict(
            self.state,
            game_loop=10573,
            units=[dict(actor, orders=[dict(ability_id=524, progress=0.02)])],
        )
        self.assertEqual(request.status(later), "started")
        # Two pre-existing orders can roll over without proving a third appeared.
        actor["orders"].append(dict(ability_id=524, progress=0))
        request = self.request(Command(524, (10,), queue=True))
        self.assertEqual(request.status(later), "pending")

    def test_targetless_addon_must_belong_to_the_requested_actor(self):
        self.data["abilities"].append(
            dict(ability_id=421, friendly_name="Build TechLab Barracks")
        )
        self.data["units"].append(dict(unit_id=37, ability_id=421))
        self.state["units"].append(dict(tag=10, unit_type=21, alliance=1))
        request = self.request(Command(421, (10,)))
        later = dict(
            self.state,
            game_loop=10573,
            units=self.state["units"] + [dict(tag=11, unit_type=37, alliance=1)],
        )
        self.assertEqual(request.status(later), "pending")
        later["units"][-2] = dict(tag=10, unit_type=21, alliance=1, add_on_tag=11)
        self.assertEqual(request.status(later), "started")

    def test_constructing_reactor_is_seen_before_attachment_finishes(self):
        self.data["abilities"].extend(
            [
                dict(ability_id=3683, friendly_name="Build Reactor"),
                dict(
                    ability_id=422,
                    friendly_name="Build Reactor Barracks",
                    remaps_to_ability_id=3683,
                ),
            ]
        )
        self.data["units"].append(dict(unit_id=38, ability_id=422))
        self.state["units"].append(
            dict(tag=10, unit_type=21, alliance=1, position=[47.5, 125.5])
        )
        request = self.request(Command(3683, (10,)))
        later = dict(
            self.state,
            game_loop=10573,
            units=self.state["units"]
            + [
                dict(
                    tag=11,
                    unit_type=38,
                    alliance=1,
                    position=[50, 125],
                    build_progress=0.01,
                )
            ],
        )
        self.assertEqual(request.status(later), "started")
