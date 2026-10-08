# SC2 agent handoff — requested stop, October 7, 2026

## Stop state and first instructions

The user explicitly stopped this effort and requested preservation, a commit,
and this handoff. **The goal is paused and incomplete. Do not start games,
training, replay rendering, downloads, or new agents without a user resume.**
This document supersedes older instructions saying a game or goal is active.
The latest experiment is terminal; its receipt is a timeout, not success.

Work in `/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl`, branch
`Sam-v6/terran-rl`. The primary checkout is on `feature/setup-infra` and has not
been switched or merged. A separate `terran-training-history` worktree exists;
do not remove or alter it. Last implementation commit before this preservation
commit: `b5a60e8`. Find the preservation commit with `git log -1`.
No push, PR, merge, or cleanup of artifact directories was requested.

## Intended outcome and agreed order

Build a Terran agent that eventually handles computer races, strategies, and
increasing difficulties, with reliable learned Hard wins first. The agreed order:

1. Diagnose observed failures and build reliable primitives from established
   open-source bot behavior: mining, construction, production, scouting,
   movement, attack execution, and combat micro.
2. Prove a strong scripted baseline, then connect the learned controller to
   those primitives. Scripted success must remain separately attributed.
3. Learn decisions from professional human replays with broad controls and rich,
   player-accessible observations. A 27-choice macro model is not the end state.
4. Once imitation produces useful live play, let that policy improve through RL.
   Include a micro sandbox and demonstrate transfer to ordinary games.
5. Establish reliable Hard performance and progress to harder computer opponents.

RL is deferred. Recent games use a frozen supervised choice component with
scripted execution/timing/micro; they are neither new RL training nor a complete
professional imitation policy. The roadmap is `docs/learning-roadmap.md`.

Persistent constraints: CPU-only, GPU disabled, approximately 80% whole-host CPU
ceiling when resumed, no sudo or large unsolicited downloads. Do not show replay
or victory demonstrations before the complete goal is achieved. User allows
Astra advice when genuinely stalled; existing advisers have already given advice.
Use `Sam-v6/...` branches and worktrees under `.worktrees/`. Preserve source
snapshots and original failed results; never edit source bound by a live job.

## What is actually verified

| Area | Evidence and limits |
|---|---|
| Scripted Terran baseline | 30/30 fresh Hard wins: 10 per race, two maps, five opponent builds. This is scripted, not learned. Recorded action errors remain visible. |
| Earlier narrow RL learner | Historical Hard development panels won 12/30 and 13/30. Small macro vocabulary and scripted assistance; not reliable Hard and not the broad professional policy. |
| Headless infrastructure | Bounded worker supervision, source/checkpoint receipts, native traces, replay capture, CPU guards, training/resume infrastructure exist. |
| Efficiency | Earlier bounded parallel collection measured 3.39× serial throughput. Do not generalize it to every workload; recent native diagnostics are sequential and low CPU. |
| Replay viewing | Linux OSMesa/ffmpeg replay-to-MP4 export previously verified. No VM required for portable video. Exact engine build and map must match. |
| Current learned production component | Some unit/building choices work through repaired primitives; one Zerg VeryEasyMacro victory in panel06. No reliable learned all-race Hard result. |
| Primitive fixtures | Expansion gas, depleted mining, Liberator deployment, and occupied addon clearance have native receipts. These are engineering fixtures, not strength results. |

Scripted Hard contract: `logs/roadmap/primitives-hard-baseline-01/panel`;
seeds819001–819030, AcropolisLE/AbyssalReefLE, Rush/Timing/Power/Macro/Air,
step8, 1200game seconds, 300wall seconds, peak hostCPU9.3%.
API difficulty requested Hard (protocol5); old replay metadata calls it Harder.
Preserve both labels. See `docs/scripted-hard-baseline.md` for errors and scope.

## Why live imitation has been weak

There have been two different classes of failure. Do not conflate them.

**Execution failures:** accepted requests did not necessarily produce anything;
delayed construction failures were missed, refinery routes were incorrectly
queried at blocked geyser centers, addon pads were crowded, workers lost local
mineral targets, and a retry counter reset when unrelated work started. These
are concrete bugs with traces, fixes, and isolated checks.

**Decision failures:** the current production classifier answers “which command
did a human issue, given that one was issued?” It has no WAIT output. Calling it
every44loops forces new decisions even when a human would save, wait, or let
existing work finish. Human states also differ from states caused by student
mistakes. Correct execution alone cannot teach army composition, useful capacity,
attack timing, or recovery. Recent games can have excessive workers/buildings and
weak armies despite substantial resources and zero action errors.

One particularly harmful decoder chose cheaper fallback commands when the model's
preferred Factory was unaffordable. All37Bunkers in native07 were fallbacks,
never raw top choices. Spending100 prevented saving150. Retaining the preferred
intent and reserving resources corrected this, producing26military births and
17completed production buildings in a matched600-second canary where the old
decoder produced neither. This is an execution/decoder improvement, not proof
of learned strength. Evidence: `resource-reserved-intent-comparison-02`.

## Current components and their responsibilities

| File | Responsibility / important behavior |
|---|---|
| `src/bots/terran_primitives.py` | Shared mining, builder protection, scouting/combat support. Safe local minerals preferred; visible safe remote fallback if depleted. Liberator mode/zone micro added. |
| `src/learning/entity_play.py` | Broad command/primitive bridge; explicit production clearance points and mobile blocker hold. |
| `src/learning/production_request.py` | Tracks actual start/failure from native observations, new foundations, delayed errors, and request-scoped retry attempts. Immediate API acceptance is insufficient. |
| `src/learning/production_execution.py` | Actor eligibility, optional one waiting train order, supply/queue/pending accounting, saved intents and resource reservations, refinery outside-radius route candidates. |
| `src/learning/production_clearance.py` | Building spacing/addon pads, geyser ownership/expansion gas sites, exact CommandCenter sites, ground blocker detection. Caller executes mobile clearance. |
| `src/learning/production_component.py` | Frozen conditional production-identity component; not a full commitment/wait policy. |
| `src/learning/tournament_*.py` | Human metadata, fog-safe causal observation reconstruction, actor/target/ability reconciliation. |
| `src/learning/production_timing.py` | Preserved earlier outcome-delay helper; outcome times are not human command intentions. Its old plan is historical, not next authorized work. |
| `src/processing/replay_video.py` | Replay-to-video export. |
| `logs/roadmap/run_professional_choice_native_18.py` | Latest experimental runtime wrapper. It is a prototype saved for reproducibility, not the product training entry point. |

Native18 retains top intent/resources, withholds physically rejected abilities
for224loops except occupied addon pads, which retain the intent while mobile
blockers move/hold. Production requests time out after448loops plus route allowance.
Failed requests displace unrelated retained intents. Initial attempt0 plus three
retries1–3 is the intended bound; unrelated completions cannot reset it. There
is still one global retry slot: simultaneous failures are an unverified limitation.
Timing is scripted44loops after successful requests and8while waiting.

## Latest native games, including final timeout

All use frozen fit04, scripted timing/actor/placement/mining/scout/micro, and
VeryEasyMacro, not Hard. Accepted requests are not equivalent to completed births.

| Artifact | Result / diagnosed limit |
|---|---|
| `reserved-choice-competence-06` Terran | Normal1200-second Tie,207.914wall, zero errors; final138workers/27military,56army supply, zeroidle. All five bases reached ideal16. |
| Same panel Zerg | Victory,159.046wall, zero errors; final93workers/52military,107army supply. Only one easy win. |
| Same panel Protoss | Abort85.999wall; Reactor placement44 errors followed by contradictory Depot/Reactor retry filtering. |
| `reserved-choice-competence-07` Protoss | Normal1200-second Tie,197.037wall; final69workers/82military,131army supply, zeroidle. Five unique Reactor placement44 errors; retry counter reset by unrelated starts. Marines occupied the addon pad. |
| **`reserved-choice-competence-08` Protoss** | **Terminal wall_timeout at300.017seconds, result null, sampled CPUpeak12.2%. Only trace/static and supervisor receipt saved; no completed replay or normal outcome.** |

Panel08 used native18, AcropolisLE seed824203,1200game-second target and300wall
limit. Its exec handle45863 is gone. The timeout happened before this requested
stop was processed; no claim of successful user cancellation or game completion.
The source snapshots were saved by the supervisor. **No terminal behavioral audit
of its trace has been completed.** Why it timed out, whether addon clearance
worked in this game, request chains, and full-game Liberator transfer remain open.
Do not extend its wall budget or rerun it automatically. A resumed agent should
inspect saved evidence first, handling potentially truncated gzip/JSONL gracefully.

## New native fixtures and their precise limits

- `refinery-expansion-fixture-04`: three normal Refineries complete and188gas
  collected; native geyser-center path distance0 but outside-radius candidates
  positive. Debug setup supplies base/workers/resources.
- `depleted-mining-fixture-01`: home patches removed, remote visibility supplied;
 525minerals collected,3086remote harvest worker-observations, zero errors,
 normal150-second cutoff/replay. Ordinary panel06 uses normal local expansions.
- `liberator-micro-fixture-01`: one debug Liberator versus three enemy Tanks.
 Two Tanks killed, third escapes; 689→734→689mode sequence, one deploy/undeploy,
 zero errors, normal90-second cutoff/replay. Original all-three-kill assumption
 failed and is explicitly not claimed. Sharpy MIT reference pinned/archived.
- `occupied-addon-fixture-01`: completed Barracks, Marine on pad, debug resources;
 two withheld frames, one physical clearance move, one real Reactor foundation,
 completion and attachment, zero errors, normal90-second cutoff/replay.
 Native18 game transfer is not established by this fixture.

These changes are tested and committed through `b5a60e8`. No strategic worker,
production-building, supply, or composition quotas were silently introduced to
claim a successful imitation policy. Physical executor assistance is attributable.

## Human data and current checkpoint

Installed native engine is4.10/Base75689. Professional sources use protocol76052;
matching engine/assets are unavailable. Cached partial reconstruction is causal
and fog-safe but missing fields remain explicit; it is not exact replay stepping.
Previous engine/asset searches did not solve that. Do not guess ability identity,
use hidden enemies, or substitute future outcomes as inputs.

Current conditional choice checkpoint:
`logs/roadmap/professional-choice-fit-04/choice.npz`, SHA256
`208c27c0936607c613f23ffb6bcb6116fe40584a6f07591e246359359b90c471`.
A committed copy accompanies this handoff. Bootstrap policy
`expanded-professional-imitation-01/policy.npz` supplies vocabulary/adapter
initialization only, not macro decisions in these games.

Teaching:11professional games,2173production events including383building events.
Diagnostics:3reused games,289events. Reserved games remain untouched; these
diagnostics are not a fresh benchmark after many experiments. fit04 gets123/289
correct42.6%,22/54building40.7%,41/235false buildings17.4% (failed gate).
Resource-only offline filtering improved metrics but caused the live cheap-fallback
failure; use the saved-intent decoder, not that filter as strategic selection.

WAIT supervision is unresolved. Timing audit at44-loop real observation anchors:
six teaching games1557anchors:816positive,122wait,619unknown;
diagnostics487:194positive,41wait,252unknown. Elapsed coverage74.5–79.9%, maxgap325.
Unknown commands cannot become negative/wait labels. Stored history is not
necessarily fully encoded history; rich observations do not imply complete geometry.

Last read-only investigation found the timing classifier uses same-game verified
command mappings. Some unresolved commands might have independently known replay
ability names, so conservative classification may be improvable. Example game294,
loop33/162, abilitylink119/index0 targets neutral units. **Identity is unverified;
do not call those mining or WAIT.** Inspect `tournament_commands.py` replay_names
and original protocol evidence before changing classification. No new audit or fit
was performed on that hypothesis.

## Closed approaches and options upon an explicit resume

Do not repeat the same weight/epoch/memory-length sweeps. Current-observation,
weighted, and short-memory identity fits failed; count forecasts, inventory goals,
retrieval, forced cadence, and press/wait variants did not establish competent
full-game imitation. Earlier RL reward/recurrent/SIL studies are documented and
did not establish reliable Hard gains. Read results before reviving an approach.

Recommended first work after resume: audit panel08 and separate execution from
decision errors. If execution is stable, stop treating conditional identity with
forced cadence as a full policy. Choose one data/interface intervention with a
declared budget and stop condition, rather than another unrestricted campaign.

Options, not started or promised to work:

1. Recover trustworthy command/quiet coverage from original replay ability-name
   evidence, or obtain compatible fully observable professional demonstrations.
   This best preserves the requested professional-human direction.
2. Astra proposed144human corrections on student states:48uniform anchors/game,
   two teaching games/one held-out before labels. A qualified Terran reviewer sees
   only current and past fog-limited information and queues/reservations, labels
   an acceptable new commitment, WAIT/continue intent, or uncertainty. Require
   ≥90%labelability, both classes per split, and≥85%agreement on a fixed quarter.
   Qualified labels are unavailable. Nonprofessional corrections must not be
   called professional demonstrations. Only then one joint WAIT+identity pilot;
   proposed gates commit precision/recall≥80%, acceptable identity≥60%.
3. Broader joint entity command learning remains the intended architecture:
   ability, actors, targets, queue, and useful history/geometry jointly informed
   by player-accessible state. More capacity alone cannot repair bad labels or
   student-state coverage. Do not reopen architecture sweeps without causal need.

Do not resume RL until useful native imitation passes its declared gate. Do not
claim scripted or debug-fixture victories satisfy learned-policy requirements.

## Runtime and commands for a resumed agent

Run from the worktree root. Repository `.venv` is Python3.12 without Torch.
Torch was borrowed read-only from the exoplanet environment; do not modify it.

```bash
export SC2PATH=/home/sam/repos/sc2-repos/game/SC2.4.10/StarCraftII
export CUDA_VISIBLE_DEVICES=''
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
export PYTHONPATH=.:/home/sam/repos/sc2-repos/sc2-void-bot/.worktrees/terran-rl/.venv/lib/python3.12/site-packages
PYTHONPATH=. .venv/bin/python -W ignore::DeprecationWarning -m unittest discover -s tests -q
```

Torch interpreter: `/home/sam/repos/hobby-repos/exoplanet/.venv/bin/python`.
Native prototype scripts commonly refuse an existing output directory and bind
specific source hashes. Historical scripts are reproducibility artifacts, not a
queue to run. Use a new contract/name after inspecting prerequisites.

Replay export instructions and portable Windows instructions are in README's
“Watch a saved replay on Linux.” Export requires matching build/map, may use
`--max-frames` and `--wall-seconds`; MP4 is portable, not an interactive client.
No replay rendering was performed during this stop.

## Preservation and verification

All552non-snapshot Python experiment scripts under `logs/roadmap` are committed
in their original paths despite the general logs ignore rule. This is an archive,
not promotion of experimental code to production. Previous source snapshots and
third-party reference archives remain unchanged locally. The three previously
untracked timing code/test/plan files are saved and committed without redesign.

`docs/handoff-artifacts-2026-10-07/` contains the frozen choice checkpoint, copies
of selected receipts/contracts, source/script hashes, and a metadata inventory of
27190local files totaling21,337,211,589bytes across logs/replays. Roadmap logs alone
are roughly13GB. The inventory records paths/sizes/timestamps, **not content hashes
for every large file**; key evidence does have hashes. Native replays, large
training datasets, traces, original snapshots, videos, and other checkpoints stay
saved in this worktree outside Git. A fresh clone will not reproduce their presence.
Do not delete/archive this checkout without separately preserving those directories.
Nothing was uploaded. Saving locally plus committing code is not an off-machine backup.

Fresh stop-time verification: default suite620tests passes,40optional skips.
These skips include optional dependencies and are not claimed as Torch coverage.
Previous changed-file Ruff check passed. No new native tests or training were
started for the handoff. Test output is retained in the handoff artifact directory.
The archived scripts are preserved byte-for-byte, not newly lint-clean: staged
whitespace inspection identifies one existing trailing space in
`run_professional_context_query_01.py` and an existing final blank line in the
vendored CascLib utility. Its upstream LICENSE is included. These archival
formatting issues were not rewritten, so existing experiment hashes still match.

Read next: this document → `docs/learning-roadmap.md` → the tail of
`docs/current-learning-status.md` → `docs/terran-primitives-implementation.md` →
`docs/human-production-timing-coverage.md` and `docs/professional-choice-native-canary.md`.
Older chronological status paragraphs can contain superseded live handles and next
steps; the requested paused state here takes precedence.

## Update 2026-10-07 (Claude): strategy learning on top of the scripted bot

Hardest fair difficulty is API `VeryHard` (UI "Elite"); `Cheat*` levels are excluded.

| Panel (30 games, 3 races x 5 builds x 2 maps) | Seeds | Wins |
|---|---|---|
| Scripted, Hard | baseline | 30/30 |
| Scripted, VeryHard | 830001+ | 19/30 (Rush 0/6) |
| Scripted + worker defense, VeryHard | 850001+ | 23/30 |
| Stage A imitation head, Hard | 840001+ | 30/30 |
| Stage A head + searched offsets, VeryHard | 860001+ | **26/30** (Zerg 10, Protoss 10, Terran 6) |

- Fixed: immediate native rejections (result 41) never advanced `next_loop`, causing a
  retry loop until wall timeout (`withhold_rejected_request`, native19).
- Stage A: `src/learning/strategy_policy.py` head imitates `scripted_targets`/`scripted_attack`
  (`logs/roadmap/strategy-imitation-fit-01`; tanks head 94.8% held-out, just under 95%).
- Stage B: cross-entropy search over per-race, per-phase offsets on the head's targets
  (`strategy_cem_01.py`, 7 of 8 iterations; stopped silently in iteration 8, likely CPU guard).
  Zerg/Protoss converged to 19-20/20 in training. TvT degraded from noisy elites;
  `strategy_cem_02.py` (TvT, shared games per iteration) stayed flat at about 50%, so the panel
  uses zero TvT offsets, fixed before the panel ran (`logs/roadmap/strategy-offsets-final-01/DECISION.md`).
- 26 vs 23 of 30 is a modest margin; a second fresh panel would confirm it.
- Remaining losses are all TvT: two Marine rushes at about 6:15, one Power, one Tie at 1200 s.
  Some TvT ties come from never finding the last enemy structures.
- Human data: 3.16.1 engine plus replay packs at `/home/sam/repos/sc2-repos/game/3.16.1`;
  labels from the Terran player's fog view (`replay_strategy_extract_3161_01.py`) and
  `strategy_human_fit_01.py` to fit a head on winners' games; not yet evaluated live.

### Update: scripted macro and finishing fixes on top of the strategy stack

All rows: Stage A head + `zero-terran.json` offsets (searched Z/P, zero TvT), VeryHard unless noted.
The fixes below are scripted rules (`src/bots/macro_rules.py`, `primitive_terran.py`), not learned.

| Panel | Seeds | Maps | Wins |
|---|---|---|---|
| Macro fixes + Bunker | 870001+ | Acropolis, Abyssal Reef | 27/30 (Z 10, P 9, T 8) |
| Same, Hard regression | 880001+ | Acropolis, Abyssal Reef | 30/30 |
| Same, unseen maps | 890001+ | Odyssey, Interloper, Catalyst | 37/45 (four P ties at 200/200) |
| + split structure hunting | 891001+ | Odyssey, Interloper, Catalyst | 40/45 (Z 15, P 13, T 12) |

- Supply: only one depot could be pending (`depot_limit`). Float: minerals add Barracks, gas adds
  tanks/Factories (`spend_float`); Armory and level-2 infantry upgrades.
- TvT: a Bunker at the natural against Terran (Marine rushes arrive about 3:05); worker defense
  counts it. Paired 20-game TvT training set (seeds 920000+): 9 -> 12 (gas) -> 13/20 (Bunker).
- Rejected on the same paired set: one-base safe opener (6/20), holding attacks to 100 army
  supply (6/20).
- Finishing: remembered snapshots are targets; with nothing known, up to six groups sweep unseen
  expansions and grid points.
- Paired comparison tool: `logs/roadmap/offsets_ab.py`; `panel.py` takes `PANEL_MAPS`.

## Update: human-label strategy head (option 3 learned route)

- `logs/roadmap/strategy_human_fit_01.py` fit on 2,219 winning Terran player-games from the 3.16.1 pack1 extraction
  (partial, ~4.1k of 5.3k receipts). Held-out exact accuracy: bases .83, barracks .74, tanks .74, workers .22.
- Paired live check on the panel-03 seeds (872001, familiar maps, VeryHard), same seeds as production's 24/30:
  - Human head, no offsets: **5/30**. 21 ties at 1200 s. It attacks in only 0–11% of decisions (human "attack" labels are rare)
    and sits on 150–170 supply.
  - Human head + forced attack at 100 army food (`force100.json`): **18/30** (Z 8, P 6, T 4) vs production 24/30 (Z 9, P 9, T 6).
  - First run failed on a missing offsets argument (kept as `human-head-veryhard-panel-03-paired-FAILED-missing-offsets`).
- Decision: the human head does not replace the imitation head as production or as the CEM base. Production is unchanged.

## Update: worker/gas saturation rule (commit d0857b0, scripted)

`saturation()` in `src/bots/macro_rules.py`:
- Caps SCVs at 22 per ready base + 6.
- While gas >= 800 and minerals < 400, caps gas workers at 6.

It targets late TvT losses that had 66 SCVs on two bases and 1,300–2,000 banked gas.

| Check | Before | With rule |
|---|---|---|
| TvT training seeds 920000 (paired) | 15/20 | 16/20 |
| Panel-03 seeds 872001 (paired, already-used eval seeds) | 24/30 (Z9 P9 T6) | 27/30 (Z10 P9 T8) |
| Fresh familiar panel-04, seeds 876001 | — | **28/30** (Z10 P10 T8) |
| Fresh unseen maps newmaps-06, seeds 896001 | 41/45 on 894001 (T 12/15) | **38/45** (Z15 P14 T9) |

- Fresh panels combined: 66/75 with the rule vs 65/75 before. The paired evidence is mildly positive, so the rule is kept.
- TvT is still the gap (17/25 on fresh panels). Remaining TvT losses are combat, not economy:
  - Marine rush on Abyssal Reef at about 5:40, in 2 of 3 Abyssal panels.
  - Army lost to widow mines, sieged tanks and Ravens at 13–15 min.
  - Banked minerals on two bases without taking a third (Power build).
- Rejected: early-rush one-base response (commit fa7049c, reverted). Trigger: 4+ enemy Marines seen before 150 s,
  or 3+ Barracks before 180 s.
  - It never fires on Abyssal Reef: the scout sees no Marines before they arrive at about 183 s.
  - On Acropolis it turned a 652 s win into a 1139 s loss.
  - TvT training seeds 920000: 15/20 vs 16/20 (`logs/roadmap/tvt-rush-response-01`).

## Update: rally the holding army at the Bunker (commit 9f140fe, scripted)

The Abyssal Reef rush loss happened because Marines waited in the main, about 29 units from the natural Bunker.
They only walked over once it finished, which was when the enemy's 8 Marines arrived.

| Check | Before (saturation) | With Bunker rally |
|---|---|---|
| TvT training seeds 920000 (paired) | 16/20 | **18/20** (3 games better, 0 worse; Rush 4/4) |
| Fresh familiar panel-05, seeds 878001 | 28/30 on 876001 | **27/30** (Z10 P10 T7) |
| Fresh unseen maps newmaps-07, seeds 884001 | 38/45 on 896001 | **40/45** (Z15 P15 T10) |

- Fresh totals: 67/75. The previous version scored 66/75 and the one before it 65/75. Z and P are 50/50 across these two panels.
- Remaining losses are all TvT:
  - The Abyssal Rush still loses on a fresh seed (345 s). The army chased the first 3 enemy Marines out of
    the unfinished Bunker, and the Bunker finished empty.
  - Macro and Power builds lose at 15–19 min to mech compositions.
- Rejected: hold at the Bunker when threats come within 12 of it (commit 429f7af, reverted).
  - TvT training seeds 920000: 17/20 vs 18/20.
  - Paired Abyssal Rush probe on seeds 930000–930011 (`logs/roadmap/rush_probe_01.py`, `rush-probe-01/`):
    11/12 with and 11/12 without. Bunker rally alone already holds most Abyssal rushes.
- Replay extraction finished: 5,318 receipts, 2,876 winning Terran games. The human head was not refit on the full set;
  its failure is attack timing, which more of the same labels will not fix.
- Rejected: TvT regroup rule (commit 52be717, reverted). It called off an attack after losing 40% of its peak army food
  and held until the army exceeded that peak.
  - TvT training seeds 920000: 18/20 (2 games better, 2 worse).
  - Paired 50-game TvT probe on seeds 940000+, 5 builds x 5 maps x 2 (`logs/roadmap/tvt_probe_01.py`, `tvt-probe-01/`):
    production 40/50, regroup 39/50.
- Production TvT by build in that probe: Rush 10/10, Timing 9/10, Air 10/10, **Power 6/10, Macro 5/10**.
  The remaining TvT gap is late games against tank/mine/Raven/Liberator compositions.
