# Status at the requested pause

No simulations or training are running. The six-case physical batch is terminal;
the reviewed24game matched comparison has not been prepared or started.
The goal is paused at the user's request, not achieved.

## What is working

- Repository/package/environment discovery, supervised headless execution,
  training/resume/checkpoint provenance and retained game artifacts are in place.
- Real short-episode parallel collection measured3.39times serial throughput;
  logging/vectorization microbenchmarks improved separately. These are bounded
  measurements, not a promise of that speedup for every training workload.
- Linux replay-to-MP4 export using existing OSMesa/ffmpeg was previously verified;
  native replays and nonempty videos remain saved. No new replay viewing occurred.
- A learned Terran macro policy already wins Hard games against all three races.
  Retained development panels are12/30and13/30wins (40–43%), with substantial
  variation across race/build/map. This is not reliable all-race strength.

Evidence: README.md:69–119, docs/performance-baseline.md:95–132,
docs/experiment-results.md:150–160 and its October5status section.
Retained checkpoint is logs/ppo-combat-kills/frozen-easy40.npz,
SHA2560f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6.

## What has not worked

Numerous small reward/optimizer/observation/control experiments either regressed
or failed their comparative gates. Intermediate kill rewards are implemented,
but additional collection shaping learned economy without an army and failed
combat transfer. SIL's offline improvement did not improve actual Hard wins.
Recurrent training completed128games/256sequence updates per arm, then90fresh
evaluation games; greedyHard wins were4/12recurrent,5/12reset,5/12reference.
The study establishes no memory benefit under its64training-games-per-arm setup,
not that memory is useless.

Evidence: docs/experiment-results.md:24–111,
docs/superpowers/plans/2026-10-05-recurrent-strength-results.md:10–35.

The literature-inspired teacher bootstrap reached a real native feasibility
test:8/12Hard wins, but Terran1/4fails the all-race competence gate. This is
scripted training-target evidence, not learned strength. The separate four-game
trace showed actual medivac healing and inappropriate tank siege near air-only
targets. Its incidental wins cannot revise the earlier gate. Small panels are
noisy; neither one failed race panel nor a few diagnostic wins establishes a
reliable success probability.

Evidence: docs/superpowers/plans/2026-10-05-macro-teacher-results.md:10–26,
docs/superpowers/plans/2026-10-05-micro-order-results.md:7–24.

The isolated tank correction has native physical support. Original fixture
validation failed on SupplyDepot lowering; an independent semantic audit
preserves the failure and verifies all six recorded physical requirements.
Its effect on ordinary gameplay is still untested. Latest physical CPU windows
average10.50%,peak14.68%; no GPU, sudo or heavy download was used.

Evidence: docs/superpowers/plans/2026-10-05-ground-tank-physical-results.md:3–36;
logs/audit/ground-tank-fixture-complete-independent-review.json.

## Distance from the goal and choices

Engineering delivery is much further along than learning performance. We have
occasional learned Hard victories, not reliable varied-opponent competence or a
demonstrated route to higher difficulties. The working final check is21/30wins
on untouched Hard cases balanced across races; that bank remains unused.
There is no defensible completion percentage or ETA for the learning gap.

My assessment: the effort became too fragmented across small experiments and
validation infrastructure. That exposed regressions but did not establish a
competent initialization and stable learning campaign early enough. More of the
same overnight training is not justified by the results. This is an assessment
of our approach, not a measured allocation of total time or a skill bug claim.

1. Recommended: finish the bounded tank comparison, establish a demonstrably
   competent teacher/human-replay corpus, imitate into a learned policy, then
   run one coherent RL campaign with milestone evaluations. Teacher competence,
   clone competence and improvement from RL are separate gates. Human/scripted
   strategy knowledge enters training; deployment macro remains learned.
2. Favor strategy discovery: constrain the first task to one map/opponent/style,
   prove stable PPO learning there, then expand race/build diversity. This changes
   the development sequence, not the final all-race objective. It avoids relying
   on scripted macro demonstrations but likely needs more experimentation.
3. Revisit representation/actions: stronger unit/entity observations and learned
   hierarchical macro may be necessary for higher difficulties. Test them against
   a competent baseline first; the failed recurrent study does not justify
   immediate full AlphaStar-scale machinery or more hardware.

The literature and its practical limitations are recorded in
reports/SC2 RL practical improvements.md. No training or new bank should resume
until the user chooses to resume the paused goal.
