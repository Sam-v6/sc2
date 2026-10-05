# Recurrent information and native backend evidence

The literature-informed recurrent method now has a training-only information
check and a complete native collection/sequence-PPO backend smoke. Neither proves
stronger gameplay. The retained parent remains unchanged and reliable all-race
Hard performance remains unmet.

## Information diagnostic

The fixed predictor split contains60 fitting and20 held-out whole training games,
56,297/20,106 eligible causal windows. Mean Brier errors are current.12926835,
ordered.11854654 and shuffled.12544142. Ordered history improves8.29% over current
and5.50% over shuffled; both target errors improve. The declared information gate
passes. The encoder had already learned from these games, so this is held-out
predictor fitting within a prelearned representation, not unseen-game policy
generalization or a gameplay result. Errors aggregate by decision count.

The v1 loader repeatedly decompressed compressed arrays per row and was stopped
with exit130 before a result was produced. Its source and abort receipt remain
under `logs/recurrent-memory/history-v1-source` and `history-v1-abort.json`.
V2 loads arrays once and changes no statistical setting. Its single completed
result is `logs/recurrent-memory/history-diagnostic-v2.json`; independent review
`logs/audit/recurrent-history-diagnostic-independent-review.json` verifies293
bindings, split, scores and gate without fitting again. Four diagnostic tests pass.

## Actual native smoke

The fixed [smoke protocol](2026-10-05-recurrent-native-smoke.md) completed two
Medium Terran Rush games. Both lost after483 decisions/517.142857 game seconds;
their raw action/snapshot/reward ledgers matched exactly at zero residual
initialization. Both native replays, chronological2N journals, seeded choices,
ordinary reward transitions and typed trajectories passed independent review.
No videos were shown.

Each arm then performed exactly four actual whole-episode PPO updates. Independent
in-memory reconstruction matched every metric and all six learned parameter,
Adam-first-moment and Adam-second-moment arrays exactly. Clocks4,episodes/attempts1,
RNG, reward context and frozen parent match. The retained parent's complete
network stays frozen; new GRU/residual parameters have fresh optimizer state.
Whole episodes are minibatches, with full BPTT and resets at episode boundaries.
The matched control resets hidden state each decision while retaining the previous
selected action. It has the same parameterization and initialization as the
recurrent arm. This controls memory access rather than parameter count.

Smoke input SHA256:
`d0bf7d7ca51852de585a71d629d8dda3593d3636ee42b8fc82ca02004373f7c2`.
Recurrent fitted SHA256:
`dfb6c24cf87bebabf2e07d86517b86ceb584fefb00397bb351303ab732d6781f`.
Reset-control fitted SHA256:
`55ada1d663b8e603273b27aeacc0b12a4b80a85f6df3a7e2b60609b0dd911b57`.
Artifacts:`logs/recurrent-memory/native-smoke/`.
Independent receipt:`logs/audit/recurrent-native-smoke-independent-review.json`.
Its evidence-validity pass is explicitly not a strength pass. The fitted smoke
models cannot initialize the planned strength study.

CPU-only/nice10/eight-CPU affinity/one numerical thread were used.17 whole-machine
two-second windows averaged10.20%,peaked15.18%,below the80% ceiling.21 focused
checks pass across the appropriate existing interpreters:4 core,4 diagnostic,
8 policy,2 worker and3 cancellation/failure-retention checks. The game interpreter
and existing Torch interpreter have different SC2 APIs; the Torch fitter avoids
importing the game worker. No downloads or sudo were used.

## Remaining work

The [memory plan](2026-10-05-recurrent-memory.md) proceeds to a separately frozen
64-game-per-arm training comparison on balanced Medium/Hard opponents, followed
by immutable policies on fresh development panels. The complete batch controller,
case bank and fixed strength gate still need implementation/declaration before
that study starts. Macro choices remain learned; no build order, unit quota or
attack timing is supplied. Richer entity perception and competence-based
progression beyond Hard remain on the development path.
