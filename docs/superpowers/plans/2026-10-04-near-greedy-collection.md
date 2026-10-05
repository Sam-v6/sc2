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

Both frozen comparison arms are running. Main production source and retained
models remain unchanged.
