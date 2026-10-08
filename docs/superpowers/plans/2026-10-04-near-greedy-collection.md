# Near-greedy collection experiment

The earlier temperature 0.5 frozen sample scored only 1/30 and failed its
training gate. On 3,070 actual parent observations, temperature 0.05 instead
assigns the top legal action 94% mean probability in states with multiple legal
actions, compared with 50% at temperature 1. This is a conditional distribution
profile, not gameplay evidence. The critic-gradient continuation finished at
4/30; the strongest retained model remains kills-only Easy40 at 12/30.

## Predeclared comparison and training gate

Use the untouched critic-isolation initial, whose numeric state is exactly the
retained Easy40 state. Hold its victory-credit reward and critic graph context
fixed. Copy its source and change only categorical temperature to 0.05 in
NumPy sampling and Torch PPO likelihood/entropy. No macro or micro recipes change.
Preserve parameters, Adam moments, RNG, counters, cadence and all other settings.

Run a fresh matched frozen sampled Hard30 comparison at temperatures 1 and
0.05: seed 20000, both maps, all three races and five fixed builds, 1200 game
seconds/300 wall seconds, four workers per arm. Verify schedules, policy seeds,
source hashes, rewards and immutable checkpoint bytes. These reused cases are
for development only.

Authorize one bounded Hard40 training continuation only if temperature 0.05
wins at least four games and at least two more than the matched temperature-1
control. This allocates experiment effort; it is not statistical proof or
acceptance. If it qualifies, first complete isolated train/resume/frozen smoke
checks, then train from the untouched initial at seed base 30000 with four
workers and the same opponent schedule. Preserve batch checkpoints and evaluate
both final greedy and sampled behavior. If the gate fails, do not train this arm.
The reliable Hard target stays 70% across the documented frozen30 suite; fresh
seed 50000 remains reserved. Do not promote weaker models.

## Verification before gameplay

The three temperature tests failed before implementation. The corrected isolated
archive passes 85 tests, including distribution/mask odds, finite-difference
likelihood gradients, strict checkpoint context and actual Torch update/resume.
Source: `logs/audit/ppo-near-greedy-source`. Migration changes only metadata
`settings.temperature=0.05`; every numeric array and every other metadata field
matches the untouched critic-isolation initial. Receipt:
`logs/ppo-near-greedy/migration.json`. Immutable initial SHA-256:
03633df9bcc83d4c5fab38118e81f1bace82a20030ddaecdf55a943f3777b64a.

Independent review reran all 85 tests and found no material defect. It confirmed
only the declared temperature source changes, exact migration, strict context
and identical greedy choices on 406 logged states. Temperature 0.05 multiplies
likelihood derivatives by 20 and reduces exploration; later clipped Adam updates
may behave differently. Frozen performance alone cannot establish learning benefit.

Both frozen comparisons completed without failures. Temperature 1 scored
0 wins, 28 losses and two horizon ties; temperature 0.05 scored 10 wins and
20 losses. Opponent and policy seed schedules match exactly, and only the two
declared source files differ. Checkpoint hashes stayed unchanged. Every reward
component and seeded categorical action on its actual observed state passed the
audit. Nonforced greedy agreement rose from 52.5% to 91.7%. Receipt:
`logs/audit/near-greedy-frozen-comparison.json`.

The predeclared gate passed. Separate two-game train/resume/frozen sampled
checks completed without failures (all six reached their 120-second horizons).
Hashes chained across resume, frozen bytes stayed exact, and finite payloads
advanced from 144/676 to 148 episodes/attempts and 684 optimizer updates. Context,
cadence and untouched experiment initial/canonical input were verified. Receipt:
`logs/audit/near-greedy-smoke-results.json`.

Hard40 completed from the untouched initial with 10 wins and 30 losses, without
failures. All 24,692 transitions and every discounted return passed audit;
maximum return error was 2.49e-14. Opponent schedule matches the critic-isolation
control, and only the declared temperature source files differ. The final contains
finite parameters/moments, 184 episodes/attempts and 1,080 updates. Its immutable
SHA-256 is b55da4f1f0b8fc3bdde4cd1194319d25fd37d4f514f4cadc82d5b08d35f40ea9.
Receipt: `logs/audit/near-greedy-hard-1-results.json`.

Measured post-update divergence on actual collected states peaked in the first
batch (mean old-to-new KL 0.236, collected likelihood clip fraction 15.1%, greedy
choice flips 8.4%). Later batch KL ranges 0.0014 to 0.0131. These descriptive
measurements do not identify the cause of wins/losses. Receipt:
`logs/audit/near-greedy-update-drift.json`. Frozen greedy and sampled Hard30
comparisons of the immutable final completed without failures. Greedy play scored
14 wins/16 losses: Terran 5/10, Protoss 3/10, Zerg 6/10. Sampled play scored
8 wins/22 losses: Terran 5/10, Protoss 0/10, Zerg 3/10. Frozen hashes are unchanged.
The sampled result regresses against the migrated initial's 10/30; greedy
performance exceeds the retained numerical parent's 12/30 on the reused suite
by two wins. This is a small development gain, not reliable Hard acceptance.
Receipts: `logs/audit/near-greedy-final-evaluate-hard30-results.json` and
`logs/audit/near-greedy-final-sample-hard30-results.json`.

## New development-bank comparison

Before promoting a new preferred model or continuing its training, compare the
original retained kills-only Easy40 and this frozen final with greedy choices
on seed base 40000: the same 30 race/build/map cases, 1200 game seconds/300 wall
seconds, four workers per arm. Use each checkpoint's exact matching source;
rewards/critic context differ but do not affect frozen choices. Verify terminal
receipts, schedules, immutable hashes and source contexts. These are fresh
**development** cases; the separate final acceptance bank 50000 stays untouched.
Choose the candidate for further work only if it at least matches the baseline
on this new bank. Ties or modest counts are not statistical improvement. The
unchanged reliable Hard target must still be satisfied before acceptance.
This is collection evidence on reused cases, not improved learned strength or
acceptance. Main production source and retained models remain unchanged.

The new development-bank comparison completed without failures. Parent scored
13 wins/17 losses; candidate scored 11 wins/18 losses/one horizon tie. The
candidate failed the predeclared requirement to at least match the parent. Do
not promote or continue this trained final. Keep the original Easy40 baseline;
the 14/30 reused-bank result did not carry over. Validation audited all greedy decisions and reward components, unchanged hashes,
matching case/policy seeds and exact expected source differences. Receipt:
`logs/audit/near-greedy-validation-results.json`.
