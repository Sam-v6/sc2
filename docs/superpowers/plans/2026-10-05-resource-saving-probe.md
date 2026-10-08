# Sustained resource-saving probe

Goal: test whether a useful macro capability is missing before another RL run.
This follows the closed combined-reward and five-second unit-intent experiments;
neither is reopened. Retain the parent actor and ordinary combat objective.

## Fixed design

- Work in Sam-v6/terran-rl. Preserve all older frozen artifacts. New ignored source
  lives in logs/resource-saving-probe/source; no production code changes.
- One known-parent regression game20013, Protoss Air/Simple64, must reproduce the
  recorded canonical406-decision trajectory exactly before fresh cases launch.
  Instrumentation and availability queries must send no new game commands.
- Eight fresh parent Hard cases116000–116007; races/builds/maps cycle3/5/2. All
  games use1200game/180wall seconds, one-second macro decisions, original
  retained0f3e05 actor, ordinary combat scoring, no learning or parameter fitting.
- Select one (decision,target) per parent using a case-seeded uniform draw over
  observed eligible pairs at60–900 game seconds. Outcomes/rewards are not inputs
  to selection. Targets are existing spending actions: units, structures/addons,
  orbital morph or infantry research. Every existing nonresource legal condition
  must hold; actual affordability must fail. Record costs and both masks. Spatial
  expansion/addon checks stay ordinary queries; no prerequisites are built.
- For each eligible case run one commitment and one matched-wait branch. Both
  replay the unchanged parent until the chosen decision. Commitment suspends
  competing macro spending for at most60 game seconds, retries only when the
  chosen target is ordinarily legal, and issues it at most once. On issuance or
  timeout, resume the parent. Existing worker/combat micro and stance continue.
- Matched waiting resumes the parent at the commitment's recorded release
  decision, or remains waiting through an earlier natural terminal. If the
  commitment terminates while saving, freeze its decision count as the release
  boundary, record `terminal_before_release`, and claim no issuance/completion.
  Preserve games ending before the selected decision as `terminal_before_selection`. Until target
  issuance, its physical states must match the treatment's paused trajectory;
  failed command attempts are retained. Never select a second target/replacement.
- No eligible pair means retained no-opportunity receipt, no replacement case or
  duplicate branch games. Maximum25 actual games including the known regression.
- Keep every original one-second decision/reward transition during waiting;
  no semi-Markov training is performed. Never collapse sixty seconds into one
  ordinary discount step. Preserve terminal kill and victory feedback.
- Record native producer orders, construction tags/positions, unit birth and
  research/morph completion. Accepted-command flags alone cannot count as target
  completion. Ambiguous unit-origin attribution is not counted as proved completion.
- Freeze source, protocol, parent/maps/dependencies, independent review and banks
  before live phases. Freeze outcome-independent selections before commitments;
  freeze matched durations before wait controls. No evaluation-data fitting.
- Four engines maximum, eight allowed CPUs/nice+10, CPU-only, sampled80% ceiling
  with50% baseline gate. No downloads, installations or sudo.

## Declared mechanism gate

Require complete audits without failed/replaced active games, at least four
physically proved completed targets, and at least three distinct cases with
ordinary discounted return greater by .02 than BOTH parent and matched waiting.
Each counted beneficial case must have a proved completed target and no worse
outcome than either comparison (Victory > Tie > Defeat). The beneficial cases
must span two races and include at least one defeat-to-victory change against
both comparisons. Report every harmful intervention and lost victory as well;
externally sampled targets are not a proposed unconditional deployment policy.
Missing opportunities, timeouts and failures remain in the record. Issuance,
unit diversity, isolated reward increases or better-than-parent waiting alone do
not pass. A failed gate closes this mechanism without extension or promotion.
Passing would justify a separately declared RL interface experiment, not strength
acceptance. Reserved final bank50000–50029 remains untouched.

## Implementation checks

1. Test seeded selection is unchanged by outcomes/rewards; test commitment/wait
   state transitions, timeout, failed attempt and exactly-once issuance.
2. Test unchanged ordinary masks/parent actions with affordability instrumentation,
   native completion witnesses, real unique spawned worker, checkpoint/RNG
   immutability and forbidden learning. Review source before known regression.
3. Run known trace check, then8 parents; independently audit and freeze choices.
   Run commitments and freeze durations; run matched waits. Reconstruct all greedy
   parent choices/overrides, physical prefix states, ordinary rewards/telescopes,
   journals/replays and independently calculate the declared gate.
4. Record results with saved raw replay evidence. Do not open/show videos until
   the full user goal is complete. Only a supported mechanism
   may lead to new variable-duration RL; changed masks are a behavioral change,
   and elapsed-time discount/terminal accounting require their own tests.

## Limits

A minute without new spending or stance changes can harm economy and defense.
The parent may never create useful prerequisites. Targets are externally sampled
for this causality/capability probe, not learned macro behavior. Command failure
or uncertain unit lineage must not be turned into completion evidence. The known
trace verifies one representative instrumentation case, not all possible states.
