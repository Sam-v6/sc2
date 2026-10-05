# Self imitation bootstrap implementation and fit

The one declared offline fit is complete and independently reproduced. The declared
36-game comparison also completed and failed its development gate; the candidate
is not promoted.
The [fit protocol](2026-10-05-self-imitation-bootstrap.md) remains unchanged.

## Verified inputs and gradients

All 80 completed training episodes (26 wins/22 losses/32 ties), 77,763 transitions
and 13,157 initial positive advantages were reviewed with original seeded action
reconstruction. No evaluation trajectories are training inputs. The exact
float64 sparse archive has 7,276,587 nonzero values and is 6,931,489 bytes;
every encoded row and label was independently checked against raw ledgers.

Corrected v2 analysis passed independent NumPy derivative/inference checks.
Raw shared-body actor/value gradient norms were .0001946578/.0152807633;
cosine .0610031. The fixed .001 value coefficient makes the initial value-body
norm 7.85% of the actor-body norm. This is a starting scale decision, not proof of
what caused earlier gameplay failures or how every later update behaves.
The original analyzer's inherited-binding overwrite was corrected in a separate
source generation; its preliminary output and all prior files are preserved.

## Actual fit

- Exactly one seeded 331 shuffled epoch, 304 Adam steps, 77,763 samples.
- Learning rate .0001,eps 1e-5,value coefficient .001,gradient limit .5.
- Separately typed `sil-bootstrap` artifact with exact initial parent network,
  fresh optimizer/clocks,original combat context; zero new episode/attempt counts.
- Independent replay matched every step index,metric and parameter digest; all 18
  final network/Adam arrays,clocks,RNG/context/counters matched exactly.
- Mean parent-to-candidate KL .0001921517; per-race T .0001925219,
  P .0001759512,Z .0002091343. Both declared retention limits pass.
- Greedy training-state choices changed in 919/77,763 rows (T 296/P 299/Z 324).
- Initial/final positive support 13,157/3,639. Current-advantage actor loss fell
  .0145059→.00165661 and value loss .00171549→.0000990354, but these changing-value
  losses do not isolate policy improvement. With the initial parent advantages
  held fixed, weighted actor loss changes only .0145059→.0144795; this is modest
  training-state imitation evidence, not stronger gameplay.

Manifest `logs/self-imitation/bootstrap-run/inputs.json` SHA256:
`8f7b8db23655c8af28edf68fe3e230a42313670eb78593b439026c1da56af260`.
Final `bootstrap-run/final.npz` SHA256:
`160af0f3d0a72c8f7da5700b38cef1a01cc3b5d9135aaf6c14fd5c3845702c08`.
The retained parent remains `0f3e05d9…`, unchanged. Full receipts and step journal
are under `logs/self-imitation/`; independent fit review is
`logs/audit/self-imitation-fit-complete-independent-review.json` with 314 unique bound
files, including the independently authored audit source.

## Completed native comparison

The fixed 18 paired cases completed with 36 saved native replays, no replacement
or refitting. There were 33 terminal outcomes and three game-limit ties; no wall
timeout or worker error. All action choices, ordinary reward transitions,
chronological journals and replay headers passed the runtime validator.

| Panel | Retained parent | SIL candidate | Mean candidate return gain |
| --- | --- | --- | --- |
| Hard greedy, 12 per policy | 6 wins, 6 losses | 5 wins, 7 losses | -.0721363 |
| Easy sampled, 6 per policy | 1 win, 4 losses, 1 tie | 0 wins, 4 losses, 2 ties | -.0744050 |

Hard lost parent wins:117000,117003,117005; gained wins:117007,117009.
Hard per-race return gains T/P/Z: -.1998026/+.1461239/-.1627302.
The sampled Easy candidate loses the parent's only win. These results fail the
predeclared Hard improvement and Easy retention conditions. This bootstrap is
closed without promotion or extending its fit. It does not refute every SIL
variant, and the small panel is not final Hard acceptance evidence.

The comparison inputs SHA256 is
`e5c6c10e0660d30f72c69e8cd7026bcd94b3e1d0751a6e0e9ac17da94e3273f9`.
Evidence is under `logs/self-imitation/game-comparison/`. Independent final
review passed for all23,966 raw choices, reward transitions, chronological
journals, native headers and frozen source/model/input bindings. Receipt:
`logs/audit/self-imitation-evaluation-complete-independent-review.json`. Its
evidence-validity pass is distinct from the failed gameplay gate. Model/source/fit inputs remain immutable.
CPU observations:294 two-second whole-machine samples, mean23.30%,peak64.59%,
below the user's80% guard. Four engines maximum,CPU-only/nice10/eight-CPU affinity.
The reserved50000–50029 acceptance bank remains untouched. No videos were shown.

The next literature-informed method is a small recurrent core, described in
[the memory plan](2026-10-05-recurrent-memory.md). Its four inference checks pass,
but recurrent training and gameplay evidence are not yet available. Reliable
all-race Hard performance remains unmet.
