# Self imitation gradient diagnostic

Zero games and zero optimizer steps. Use only the independently reviewed
80-game training corpus declared in self-imitation.md. All 77,763 encoded rows
must round-trip exactly through a sparse float64 archive before analysis.

The immutable export generation is `logs/self-imitation/gradient-source` and
`logs/self-imitation/training-corpus.npz`. Its metadata binds all original inputs
and export-generation code. Preserve this generation unchanged. An initial
analyzer could overwrite inherited source bindings; its measurement is retained
as preliminary, never fitting authority. The corrected analyzer lives separately
in `gradient-v2-source`, verifies every inherited binding before adding its own,
and cannot substitute current code for the export-bound generation. Reuse the
unchanged exact archive with explicitly verified export-generation bindings.

Measure uniform full-corpus actor and value losses/gradients at the untouched
retained parent. Weight minibatch means by actual minibatch length divided by
full sample count, including the tail. Stop actor advantage gradients; record
body, actor head and value head norms and shared-body alignment. Check full-corpus
Torch/NumPy inference parity and unchanged parent parameters/files. Bind corrected
analysis code, this declaration, input archive and source generations in review.

No diagnostic gradient is a trained policy, and no norm/cosine proves gameplay
causality. Independent review precedes selecting one fixed optimizer schedule
from training-only measurements. No evaluation choices, protected games or new
SC2 runs are inputs to this phase. No source hot edits or overwrite of earlier
artifacts; CPU-only, one numerical thread under the existing low-load launcher.
