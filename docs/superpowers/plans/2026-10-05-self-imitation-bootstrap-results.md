# Self imitation bootstrap implementation and fit

The one declared offline fit is complete and independently reproduced. No fresh
SC2 games have started; neither stronger gameplay nor promotion is established.
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

## Next required verification

A read-only evaluation-worker foundation passes two tests for ordinary reward/
journal/terminal preservation and restoration after failure. Its real unique
spawn import probe completed in .628 seconds with zero games. The evaluation
source is unfinished/unfrozen: controller, case/input freeze, game validator and
independent runtime review remain necessary before the declared maximum 36 games
(12 paired Hard greedy cases plus 6 paired Easy sampled cases) can launch.

A receipt scan across the three artifact roots found no earlier uses of the
proposed 117000–117011/118000–118005 cases; preparation must recheck all relevant
case keys/artifacts before launch. The reserved 50000–50029 bank is untouched.
Training-state retention and loss evidence do not establish Hard performance.
CPU-only,one numerical thread, nice 10/eight-CPU affinity were used for offline work;
whole-machine baseline before fit was 1.3787%. A .9393% observation was taken
AFTER fit, and is explicitly not a measurement of fit utilization. Preserve raw
replays without showing videos until the full user goal is complete.
