# Can the current model learn a small set of human commands?

The weighted fit07 fails complete copying on the reused diagnostic game. Before
another architecture change or corpus expansion, test whether the same model can
learn its teaching examples at all. This is a supervised learning diagnostic,
not a held-out result or permission to resume RL.

Assumption: failure on a small, varied set warrants investigating representation,
optimization and conditional argument heads before spending more simulations.
Passing only means small-set learning works; it does not establish generalization.

- Use only corpus07's nine teaching sources and exact trainer.collect inputs.
  No diagnostic or reserved replay predictions, downloads, native games or RL.
- Deterministically shuffle each ability's teaching examples with seed8100 and
  take at most two per demonstrated ability. Bind the selected game/row indices
  and source/code hashes before fitting. Keep every original unit/target label.
- Start a fresh fit05 architecture: hidden32, refinement, actor cutoff, spatial,
  missing fields, role pooling and actor-relative points. No importance weights
  or context normalization. Same initializer seeds and Adam rate0.001/batch16.
- One run of200epochs, capped at120optimizer seconds, CPU-only/two BLAS threads.
  No extension or parameter search. Save the model and terminal command audit.
- Require at least90%complete command copying and95%correct abilities on the
  selected examples. Report all argument fields, timing and oracle diagnostics.
  Timing is not part of the complete-command gate, consistent with prior audits.
- Bind unchanged sources/code/checkpoint and record the result in the ledger.
  A failure calls for locating which argument head cannot fit; success calls
  for investigating cross-game generalization. Neither permits strength claims.

Completed one run: 62 commands across 33 abilities, 200 epochs / 800 Adam
updates in 11.98 optimizer seconds. All 62 abilities, modes and queue choices
are correct; targets 59/62 and actors 46/62. Complete copying 44/62 fails the
56-command threshold; ability passes the 59-command threshold. All 43 known
timing labels are correct. With human actors supplied as an explicit diagnostic
oracle, complete copying is 59/62. The 23 point targets have ordinary mean error
0.084 tiles. Thus small-set ability and geometry fitting work; actor selection
is the main remaining small-set failure. This does not prove cross-game ability
or target generalization. Source/code/checkpoint bindings remain unchanged.

Evidence: `logs/roadmap/professional-small-set-01/{contract,report}.json` and
its saved policy. No extension, promotion, RL or native game follows this fit.
A frozen read-only actor audit compares ordinary membership with ranking when
the human group size is supplied as an explicit oracle, to distinguish cutoff
and ranking failures before choosing a production change.

Frozen actor audit completed: exact tags 46/62, correct group size 59/62,
correct type/count composition 59/62. Supplying human cardinality to rank/top-K
only improves exact tags to 47/62. All 16 mismatches involve a single human
actor; 13 choose another same-type single actor. Eleven are SCV construction
commands, with the human SCV ranked second through eighth. Three select multiple
same-type production/research buildings. This points toward within-type ranking,
not primarily group counting. Exact identity mismatch does not prove an alternate
worker/building is functionally unusable; measure execution, travel distance and
resource/order constraints before claiming that or relaxing copying gates.
The frozen gate remains failed, and no functional competence is inferred.
Receipt: `professional-small-set-01/actor-diagnosis.json` (same selected rows,
source/code/checkpoint bindings, exact aggregate actors match terminal report).
