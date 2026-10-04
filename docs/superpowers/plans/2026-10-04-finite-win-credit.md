# Finite-match full-return experiment

Existing frozen Hard checks are weak, with many training games ending at the
1200-second match limit. The current learner treats those engine ties as
continuing-task truncations and bootstraps its critic. That is a legitimate
continuing-game formulation, but the requested evaluation counts only actual
wins within a completed test match. Test a finite-match formulation explicitly.
This is an objective/credit experiment, not a proven bootstrap bug.

1. Use a separate archived source, preserve detector actions/observations/micro,
   and keep capacity potential shaping. Reward a true win with100, defeat/draw
   with0. Treat every normal match endpoint, including the game-time limit, as
   terminal for learning with zero potential/bootstrap. Engine failures and
   wall-time supervision failures remain failures, never fabricated outcomes.
   Frozen result reporting still distinguishes Victory/Defeat/Tie and failures.
2. Set GAE lambda1 for complete discounted returns. Add observed match limit and
   remaining time so the finite horizon is explicit in the live state. Gamma
   remains cadence-aware; this optimizes discounted wins, while acceptance still
   requires the same frozen all-race Hard win rate. No macro recipes are added.
3. Add tests for all endpoint outcomes, live horizon input and the exact return
   gamma^remaining_steps * scaled_win_reward - scaled_current_potential.
   Explicitly migrate from immutable detector-initial bytes: preserve actor and
   shared parameters/moments/RNG, append zero horizon rows, reset the critic
   head/moments for the changed target, and record reward/settings/source hashes.
4. Run the full suite and real train/resume/frozen smoke separately from the
   untouched experiment input. Compare40 Easy games under matching schedules,
   maps/builds/races/eight workers; initial actor choices should match until the
   first learner update. Evaluate a retained snapshot in frozen Hard cases.
   Retain pre-batch models; do not promote weak candidates or use acceptance seeds.

The compact live representation is still an explicit first experiment. It must
not be described as the final perception system. A subsequent representation
experiment should encode observed unit type, health, position and capability,
rather than relying entirely on global summaries.

Verification: 68 tests and real train4/resume2/frozen2 completed without failures.
The eight 120-second cutoffs establish pipeline semantics only. The resumed model
has 70 episodes/attempts and 812 updates; frozen bytes are unchanged. Independent
review verified the return identity with a nonconstant critic and all migration
arrays/moments/RNG/hashes. Easy40 now uses the untouched initial bytes.
