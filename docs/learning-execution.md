# Active roadmap execution

The user resumed the roadmap on October 5, 2026. The earlier
[requested-pause status](project-status-2026-10-05.md) is a historical snapshot.
The roadmap is not complete. Keep the previous narrow macro experiments frozen.

Implementation is in `.worktrees/terran-rl`, branch `Sam-v6/terran-rl`.
The commands below run from that worktree. Run artifacts are ignored under
`logs/roadmap/`; preserve those directories when handing off or archiving.

## Current evidence

| Gate | Implemented and checked | Remaining |
| --- | --- | --- |
| A: shared controls | Raw ability, unit group, unit/point target, queue and autocast schema; full visible-map entities, scouting memory, map grids, recent commands; hidden-health checks | Broader physical command-family inventory and learned selection |
| B: replay extraction | Matching-build preflight; fog enabled; observation before command; full anonymous replay reconstructed (559 commands); source-labelled Masters trio fully reconstructed; issued-command repeats audited | Verified professional Terran games, wider corpus, issued/executed event audit |
| C: imitation | Saved CPU-only command-conditioned imitation models; whole-game/held-out-player split; raw unit groups, arguments and delay labels | Wider training corpus and useful live-game competence |
| D: micro | Native DefeatRoaches adapter using shared entities/commands; trace, scores and replay; CPU-only return-driven policy search; held-out combat-score gains; ordinary-game transfer measured | Other scenarios and successful full-game transfer |
| E: full-game RL | Existing runner/supervisor remain available | New policy RL and improvement over frozen imitation |
| F: Hard and beyond | Historical narrow learner development results remain documented | Reliable fresh all-race wins, map/build variation, harder evaluations |

The interface fixture `logs/roadmap/interface-third/` physically checked SCV
production, construction, healing, siege/unsiege, independently moved Marines
and queued orders. All nine checks and nine command results succeeded. It uses
debug setup and is engineering evidence, not learned competence.

The scripted nearest-target micro baseline
`logs/roadmap/roaches-baseline-first/` lost: 99 frames, 509 successful commands,
545.13 damage dealt, 392 damage taken, 200 killed value, 17.5 game seconds.
The first search is `logs/roadmap/micro-search-01/`, four generations of twelve
candidates, two workers, 60-game-second horizon. Hypothesis: independent targeting
and cooldown-aware movement can improve combat return without scripted timing.
Reward is killed value + 0.2 damage dealt - 0.5 damage taken + survival seconds
+ 1000 for native Victory. Stop after the bounded batch and compare on fresh seeds;
worker failures abort rather than becoming training returns. This compact linear
movement/targeting controller is an explicit initial micro experiment, not the
final broad-action Terran policy. Survival shaping can encourage fleeing; report
kills/damage separately and test transfer before promotion.

## Replay compatibility and provenance

The installed engine is Base75689 / data hash
`B89B5D6FA7CBF6452E721311BFBC6CB2`. An anonymous DI-star 4.10.0 sample successfully
stepped to its terminal result: 15,424 observations, 559 gameplay commands,
46 abilities. The raw API reports a command issued at loop t in the observation
packet at t+1; training uses the state at t-1. The API also exposes command-manager
repeat events, so its count must not be mistaken for the count of human SCmdEvent
records. Recorded commands all referenced the observed player's own units.

Compatible human sources acquired (about 238 KB total):

- [51574: Mez vs Vanya](https://lotv.spawningtool.com/51574/), Terran player 2,
  4570 MMR, TvP. The site's professional tag refers to Vanya, the Protoss opponent.
- [51573: Mez vs Sura](https://lotv.spawningtool.com/51573/), Terran player 2,
  4549 MMR, TvZ.
- [50925: Lyra vs anogashy](https://lotv.spawningtool.com/50925/), Terran player 2,
  4623 MMR, TvT.

These are Masters-level human feasibility examples, **not verified professional
Terran demonstrations**. Source URLs and SHA-256 receipts accompany the originals
in `logs/roadmap/human-replays/`. Extracted datasets are `human-51574/`,
`human-51573/`, `human-50925/`.

Named GuMiho and Bunny professional source replays were also acquired, but require
Base75025 / 4.9.3. A bounded HTTP range fetched the official old executable
(~21 MB) and small config files, leaving the original installation untouched.
The isolated runtime fails CASC asset initialization. Do not claim that binary
acquisition repaired playback, and do not download the entire 3.6 GB archive.
A bounded 52 MiB archive prefix recovered and checksum-verified the old encoding
and root manifests. An isolated overlay retained original assets through symlinks
and merged the supplemental local index entries. Native startup still failed.
An offline CascLib diagnostic decoded 701,765 root paths and verified six core
files, but also identified a missing old Liberty GameData asset. Its responsibility
for the native failure is unproved. Stop further asset acquisition without a traced
required-file failure; a missing exact replay map dependency also remains. Compatible stronger
human replay work can proceed independently. Assets/diagnostics are under
`logs/roadmap/runtime-4.9.3/` and `logs/roadmap/pro-replays/`.

Spawning Tool's date filter requires M/D/YY: ISO dates silently return unfiltered
results. Search after_played_on=8/13/19 and before_played_on=8/19/19 for the local
build's week; metadata/build and actual Terran identity still need independent
inspection before acceptance.

## Commands

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m src.learning.interface_probe --help
.venv/bin/python -m src.learning.replay_extract logs/roadmap/human-replays/51573.SC2Replay --player 2 --output logs/roadmap/example-new --wall-seconds 300 --source https://lotv.spawningtool.com/51573/
.venv/bin/python -m src.learning.sandbox --map DefeatRoaches --output logs/roadmap/baseline-new --seconds 60
.venv/bin/python -m src.learning.micro_train --output logs/roadmap/search-new --generations 4 --population 12 --workers 2 --seconds 60
.venv/bin/python -m src.learning.sandbox --policy logs/roadmap/micro-search-01/best.json --output logs/roadmap/eval-new --seed 9000 --seconds 60
```

Native execution needs local sockets and can require sandbox escalation. Use the
existing bounded process-group supervisor. CPU-only training; latest limit is
approximately 80% total machine load. A sample during two-worker search measured
11% on 32 logical CPUs; that is a sample, not a permanent limit. Do not restart
GPU work. Keep native replays; do not show victory demonstrations before the
user's goal is complete.

Latest unit verification: 123 tests passed in 9.756 seconds, saved in
`logs/roadmap/unittest-seventh.log`. Native search/extraction results must be
inspected after completion before recording gains or moving gates forward.

## First terminal learning results

All three Masters replays reconstructed to terminal results with schema-2 timing
labels: 51574 has 1,151 command-burst rows / 1,168 raw gameplay commands;
51573 has 601 / 601; 50925 has 590 / 600. Their observed controlled-unit tags
passed the own-unit audit in the checked TvZ dataset. Professional Terran identity
is still not verified for these sources.

The 48-episode micro search completed in 184.38 seconds. On eight fresh matched
seeds, the learned controller's mean killed value was 1,587.5 versus 387.5 for
nearest-target attack. Mean damage dealt was 2,401.14 versus 796.30. Five learned
runs reached the 60-second cutoff; all baseline runs lost earlier. Cutoffs are
**not victories**. Mean damage taken also increased (1,014.88 versus 526.62) as
more enemy waves were encountered. Evidence: `micro-heldout-01/panel.json`.

The ordinary-game transfer development probe held the old macro checkpoint
SHA-256 `0f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6`
fixed, comparing scripted combat against learned control of Marines within 15
tiles of a visible enemy. Seeds 99000–99002, Simple64, Hard, all three races:
scripted combat won 1/3; learned combat won 0/3. All learned micro commands were
accepted by the engine. This is a failed transfer gate, not a successful full-game
policy. Retain the checkpoint and replay evidence; do not promote it. The Marine
policy was trained only against roaches, its target-distance coefficient prefers
farther targets, and transfer changes decision cadence from four to eight loops.
These are concrete hypotheses to inspect in replay traces before another batch.
The probe code is `src/learning/transfer.py`; receipts are `micro-transfer-01/`.

## Imitation failures and label corrections

The first per-unit imitation model (imitation-03) and shared-command models
(imitation-global-01/02) failed live VeryEasy games without producing an army.
The latter issued Smart 1,414 times out of 1,417 commands. Offline prediction
accuracy is not live-game competence. No checkpoint is promoted.

Auditing original binary replay SCmdEvent records identified engine repeats:
51573 contains 195 issued events versus 601 reconstructed commands. The separate
issued-51573 dataset uniquely matches 194 events; one addon target was normalized
by the engine and conservatively excluded. The original reconstruction is retained.
51574 matches 495/505; 50925 matches 342/347. Unmatched/ambiguous events are preserved
in receipt audits, never converted to waits. Delay labels are recomputed between
retained issued commands. Controlled actors are resolved from earlier own-unit
observations, including temporarily absent gas-mining workers; no tracker or future
state enters the actor.

Models choose an engine ability first, then condition unit type/group, target,
queue and timing on that ability. All engine ability IDs remain representable.
The live adapter masks actual available abilities and uses current target tags.
Training-only normalization and class priors are saved with the model. Current
network inputs include unit composition, nearest visible enemy, economy, history
and entity attributes; full map grids and recurrent/attention encoders remain open.

The issued-command model reached the 600-second VeryEasy cutoff but still built
no army. Base-relative mirrored coordinates (imitation-canonical-02) also reached
the cutoff without an army. Neither cutoff is a victory. Canonical-01 is an invalid
intermediate fit with mismatched target coordinates; do not execute or promote it.
The next bounded experiment balances rare commands using inverse square-root
training frequency, so common movement commands cannot dominate every teaching
update. This changes teaching weights, not gameplay legality or a scripted build
order.

The balanced model (imitation-balanced-01) built one depot, two barracks and an
Orbital Command in a 600-second VeryEasy probe. Production/construction choices
were learned. It produced no army and lost all workers; the run hit the cutoff,
not Victory. This is material macro execution progress, still below gate C.
An explicitly attributed execution-assistance probe assigns each newly produced
idle SCV to visible minerals once, never overriding a current model command or
ongoing order. It does not choose worker production or buildings. Its counts and
flag are separate in episode receipts.

The newborn-only worker assistance issued zero commands: new SCVs already had
orders, and later idle workers were often previously moved by the model. Those
probes (imitation-balanced-harvest-01/02) are retained as unsuccessful diagnostics.
The current optional --idle-worker-harvest primitive handles idle workers, excluding
workers with ongoing orders or selected by the model this frame. It is explicitly
attributed and does not alter production/construction choices.
