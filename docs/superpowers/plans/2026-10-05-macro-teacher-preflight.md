# Competent macro demonstrations through the existing learner interface

Assumption: the current action/execution interface may support substantially
better macro play than the learner has experienced. Test that before another
representation change or training budget. A scripted teacher imports human
strategy into training. It is an explicit bootstrap experiment, not strategy
discovery from scratch or a deployment fallback. Future deployed macro decisions
must come exclusively from a learned policy; later RL improvement must be shown
separately from imitation. Reliable all-race Hard remains the actual goal.

## Fixed feasibility test

Use exactly TerranLearner's current27actions, ordinary masks, one-second nominal
macro cadence, game_step8, unchanged placement/worker/combat implementations,
ordinary resources/fog and combat-kills-v1 objective. The teacher reads only
causal encoded observations and the current legal mask; no assigned race/build,
opponent-hidden state, future data or evaluation trajectories enter its choices.
Translate a single documented bio/mech macro teacher to action requests; do not
execute example bots, parallel extra commands, hidden unit quotas or extra micro.
Teacher-only strategic priorities must stay inside the teacher selector.

The selector takes the first legal request in this fixed priority order:
supply depot below max(4,min(12,army*0.12)) free supply; attack at32army supply
when home is safe; retreat below10army supply when home is threatened; orbital;
workers below min(66,22*bases); first barracks; refineries below min(4,2*bases);
second base at10army supply or third at40army supply/40workers when home is safe;
barracks below min(6,2*bases) at6army supply; first factory at6 and starport at12;
factory/barracks tech labs; first engineering bay at12army supply; infantry weapons.
Then respond to observed cloak with a starport tech lab, first raven and up to
two turrets; observed air with up to four vikings when enemy air exceeds twice
the viking count; medivacs below max(2,min(4,army/16)); tanks below
max(2,min(4,army/12)); marauders below max(4,marines/4); marine; wait.
These are teacher-only thresholds using current encoded scalar observations.
The selector never issues unit commands. Native appearances include starting
units, and queued commands may be deduplicated or rejected by the engine;
neither record alone establishes successful production.

Declare12Hard games, seeds125000–125011 and policy seeds equal to game seeds.
Indexi uses race(Terran,Protoss,Zerg)[i%3], build(Rush,Timing,Power,Macro,Air)[i%5],
map(Simple64,TritonLE)[(i//3)%2]. Each race uses both maps twice. Scan allthree
existing artifact roots for case freshness before preparing. The teacher source,
thresholds, jobs, unchanged executor and maps are frozen before launching.

Competence effort gate: at least8/12victories and at least2/4against each race,
with all12valid ordinary games and no infrastructure failures. This does not
prove reliable Hard acceptance. No source edits, strategy tuning, replacement
cases, extra teacher variants or supervised/RL fitting during the bank. A failed
gate stops this bootstrap proposal and preserves blocked requests/execution
facts; failure alone does not prove that the interface is inadequate.

Use maxfourengines, eight-CPU affinity/nice10, one numerical thread, no GPU,
whole-machine80percent ceiling/50percent baseline,1200game/180wall seconds.
Preserve every actual outcome on timeout/interruption/CPUstop, with no restart
based on observation timeouts. Reserved50000–50029cases remain untouched.
Keep native replays unopened; no videos until the overall user goal is complete.

## Implementation and verification

1. Add a small teacher selector and targeted tests for legal requests, supply/
   economic/production priorities, stance stability and causal observation use.
   Check that no action bypasses the mask and no selector command executes units.
2. Add a native worker using the ordinary episode runner and exact TerranLearner.
   Record raw requested actions/masks, staged execution flags/details,
   chronological journals, observed unit/structure counts, typed full episodes
   and native replays. Issued requests do not prove completed production; record
   actual observed unit appearances separately. No optimizer calls or learned
   checkpoint mutation. Validate replay/context/reward/case/source provenance.
3. Add the bounded controller and failure-retention checks. Independent source
   review precedes freeze/prepare. Run all12once, then independently audit the
   full native evidence and gate. No optimizer replay or earlier-study reruns.

Only a passing teacher can authorize a later bounded multi-strategy training
corpus and whole-actor cloning with whole-game splits, fresh sampled-policy
checks and subsequent reinforcement learning. That later stage needs its own
fixed protocol; current failed recurrent models are not promoted or extended.
