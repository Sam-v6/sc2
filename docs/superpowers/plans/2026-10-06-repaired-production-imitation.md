# Matched human imitation test of recovered production commands

Hypothesis: omitted ordinary army production/morph commands impair imitation.
The source repair changes command labels and derived history/timing on shared rows;
this is a source-version intervention, not an isolated extra-label effect.
Compare the original and repaired six-game teaching sources with a fresh paired
GoalFirst fit. No architecture change, RL, native game, new replay, download or
reserved replay prediction is part of this test.

Original teaching: pro-demonstrations-07 games294/870/955/839/991/523 (3,398
representable commands). Repaired teaching: pro-demonstrations-production-08 for
the same six games (3,544). Held development data: original887/920/851, previously
used diagnostics, 1,113commands. This is not fresh acceptance. No774/848/51483/51886.

Use hidden64, seed8156, Adam.001, batch16,30epochs,600optimizer seconds per arm,
two CPUthreads. Both arms present3,398examples per epoch:213updates per epoch,
6,390updates and101,940presentations if complete. Repaired samples are drawn
without replacement from all3,544representable examples each epoch using independent
declared seed8157. Do not prescribe strategy or remove action families. Save every
epoch's sampled indices/hash, planned recovered coverage and actual exposure from
completed optimizer updates, including partial epochs. Sampling
only changes the source examples; all observations/history/labels remain original
causal human data. Match initial weights exactly, using union teaching-only numeric
support from both source versions. No held-label support or history corruption.

Evaluate both policies on the same full repaired teaching corpus and the same
held development corpus; also retain each arm's own teaching scores. Report ordinary
complete commands, macro ability recall/false positives, all recovered production
families, and per-game results. Own-prediction history on unchanged human states is
an offline diagnostic only. Check reload parity and independently reproduce saved
ordinary/own-history predictions and report metrics after the run.

Development gates: both finish matched30epochs; held macro recall improves by
10points and complete commands by5points; held macro false positives increase at
most5points; own-history held macro recall improves10points. On the same146new
teaching rows, recovered-family ability recall and complete-command fractions must
each improve by25points. Report Build/Train/Research diagnostic macro taxonomy
separately from the six recovered families (including Morph). Do not hide regression
behind training recall. Passing gates warrants a separately planned functional test,
not promotion or Hard acceptance. Failure/inconclusive closes the trial without
extension, seed sweep or unchanged retraining.

Freeze script/source/corpus/runtime/plan hashes and preflight initial parity,
sampling determinism, dimensions and source eligibility before fitting. Watchdog
stops above80%whole-hostCPU on three samples, or1,800totalwallseconds; no GPU.
Store telemetry and terminal status. Full-roadmap completion remains unproved.
