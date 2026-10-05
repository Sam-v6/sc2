# Verify a ground-aware tank primitive before more bootstrap training

Native observations demonstrate siege orders in neighborhoods containing only
flying enemies and no ground structures. They also refute absence of medivac
healing. Correct only the tank guard: consider visible non-flying enemy units
and structures for siege/unsiege readiness at the existing12/14ranges.
Leave economy, targeting, movement, medivac behavior, macro actions, masks,
cadence, observation schema and rewards unchanged. Scripted micro is within the
user's authorized primitives; deployed macro must remain learned.

Preserve frozen old sources and evidence. Implement the correction in an
isolated new adapter, with targeted checks for air-only, ground-unit,
ground-structure, flying-structure and siege/unsiege cases. No teacher strategy
changes. An isolated native debug-unit fixture must then demonstrate that the
old guard can siege near air-only targets, the corrected guard remains/returns
mobile there, and it still sieges for a ground target. Debug fixtures are
engineering checks only: not training, ordinary opponent wins or acceptance.
Freeze fixture cases/source before launch, use a fresh seed outside every prior
bank, and preserve failure evidence. If the physical check fails, stop before
gameplay comparison and diagnose it.

Only after that check passes, declare a fresh matched ordinary-game comparison
of unchanged teacher/executor versus the same teacher with the tank correction.
Freeze exact seed/race/build/map cases, budgets and gates before playing;
do not reuse126000or125000banks, tune strategy or count diagnostic outcomes.
Require actual all-race competence before cloning the corrected teacher, and
compare lost control wins as well as gains. A primitive fixture or scripted
victory never establishes a learned policy improvement.

Use CPU only, max4engines/eight-CPU affinity/nice10/one numerical thread,
80%whole-machine ceiling/50%baseline, no sudo/downloads. Do not open replays.
Reserved final50000–50029cases remain untouched. A later qualified demonstration
corpus, whole-actor cloning and fresh on-policy RL need their own declared
protocol, with imitation and subsequent RL effects reported separately.
