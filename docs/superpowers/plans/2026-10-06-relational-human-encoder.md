# CPU relational encoder for human imitation

Current evidence: geometry improves small-set exact actors46→52 and complete
commands44→51/62, but fails the56gate. Eight remaining errors are single-SCV
choices and two select multiple production/research buildings. Cross-game fit07
is still weak. The current encoder processes each unit independently before
averaging groups; it has no learned unit-to-unit interaction.

[SCC section4](https://proceedings.mlr.press/v139/wang21v/wang21v.pdf) uses learned
self/cross attention over unit groups and attention pooling. Apply the relational
idea as one small residual self-attention block, not a reproduction of its
architecture or data scale (even its smaller corpus has4,638games versus our9).
Do not add RL, recipes, hidden state, unit caps or restricted action choices.

Use the already installed CPU PyTorch runtime; no installation/download/GPU.
An optional encoder retains the existing NumPy parameter/forward/backward
interface and uses CPU autograd internally. Existing command heads, masks,
spatial sensing, history and optimizer remain. Attention has learned query/key/
value projections, a zero-initialized output projection and an optional learned
squared world-distance logit coefficient (initially zero, unconstrained sign).
All legitimate known entities can interact; last-seen memory stays last-seen.
This is an input representation, not a nearest-worker decision rule.

Default NumPy encoder/checkpoints remain unchanged. Save/load records the CPU
backend and relational flag. CLI opt-in requires PyTorch, with a clear error if
absent. Bind the new source file and runtime version in experiment configuration.
The optional import must not make default training require the framework.

Checks before fitting: RED→GREEN CPU/autograd parity against NumPy without
attention, residual finite differences including shared embeddings, permutation
equivariance, neighbor-dependent entity outputs, empty histories/entities, and
checkpoint round-trip. Default full suite plus explicit external-CPU tests,
Ruff/diff checks and independent review. All CPU tensors are explicit; two
threads and CUDA_VISIBLE_DEVICES empty in experimental launch commands.

First experiment: the exact62selected human rows, same seed/200epochs/800updates/
batch16/rate.001 as prior small-set checks. Run a matched CPU-backend baseline
without attention and a CPU-backend attention variant, each capped at120optimizer
seconds. Actor geometry stays disabled in both to isolate relations. Bind rows,
source/code/runtime/checkpoints before fitting. Gates: variant complete>=56,
exact actors>=56, ability62 and targets>=59. Also report matched-baseline fields,
updates/runtime and whether the variant improves complete commands. Failure
ends the experiment; success only permits a separately frozen cross-game
imitation comparison. No native games, other replay predictions or RL here.

Implementation: initial four tests RED→GREEN; added full-command-loss/Adam and
real CLI-source/runtime binding tests. Six explicit CPU tests pass0.80s; Ruff
and diff checks pass. Independent reviewer reports no actionable findings and
independently passes four parity/gradient/permutation/checkpoint tests. Default
NumPy behavior stays optional-framework-free. The mixed-runtime broad suite
hits one existing Python3.11 subprocess test: inheriting the Python3.12 NumPy
site-packages path causes a C-extension import failure. A direct import probe
reproduces it without updates. This is an environment boundary, not a claimed
green broad run; default suite result is recorded separately. No framework or
package was downloaded/installed. Both interpreters need compatible dependency
paths; do not export this temporary PYTHONPATH globally.

Completed matched comparison: both runs finish200epochs/800updates, baseline
15.78 and attention24.17optimizer seconds. Initial audits match exactly;
source/code/runtime/checkpoint bindings and schedules verify. Baseline matches
the earlier NumPy small-set result: actors46, targets59, complete44/62. Attention
gives actors47, targets62, complete47/62. Both have all62abilities/modes/queues
and43known timing labels correct. Ability/target gates pass, actor/complete56
gates fail. No extension, cross-game fit, native game, promotion or RL follows.

Frozen attention actor audit: correct count/type composition56/62, exact47;
supplying human cardinality only raises exact selection to52. Of15failures,
nine involve SCV ranking (one also predicts extra workers), one chooses another
same-type TechLab, and five rank the human actor first but include extra units.
Attention does not resolve the selection bottleneck; its exact target fitting
does not establish functional worker choice or cross-game competence.
Evidence: `logs/roadmap/professional-small-set-relational-01/comparison.json`,
both run reports/checkpoints and `attention/actor-diagnosis.json`.
