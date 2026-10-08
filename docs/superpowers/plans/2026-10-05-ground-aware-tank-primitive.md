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

The fixed physical bank is6eight-game-second Simple64 debug fixtures, seeds
127000–127005: control/candidate mobile tank against an Overlord; control/
candidate initially sieged tank against an Overlord; candidate mobile tank
against a Roach; candidate mobile tank against a SupplyDepot. Spawn one own tank
at map center and one visible enemy target6units away, leaving starting bases
intact; no macro loop runs. Use the actual complete old/corrected micro routines.
Record observed unit forms/current orders/visible target ranges and queued
commands every8game loops. Require at least6frames with the target within12.
Control must visibly siege/remain sieged against air without unsiege commands;
candidate must show at least5mobile contextual frames, never issue siege against
air, and issue unsiege from the initially sieged state. Against ground unit or
structure, candidate must queue siege and visibly become sieged. All6checks
must pass with native replays and no callback/infrastructure errors. Use2workers,
60wall seconds per fixture. These are physics checks only; no wins are counted.

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
