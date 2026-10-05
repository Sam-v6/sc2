# Amended joint-head evaluation results

Closed with failure; no extension, refitting against this bank or promotion.
The original 6.409% disagreement gate failure remains recorded; removing its veto
was an explicitly disclosed protocol amendment made after seeing that failure.

All 24 games complete without infrastructure failures. Parent 7/12 wins; candidate
6/12 wins and one cutoff tie. Mean discounted return falls .36691350 to .28500265.
All three gameplay gates fail: no two-win gain, lower return and no two-race gain.
Race win gains: Terran −1, Protoss 0, Zerg 0. Two parent victories become losses;
one parent loss becomes a victory. Reliable Hard strength remains unmet.

| Seed | Race/build/map | Parent | Candidate | Parent return | Candidate return |
| --- | --- | --- | --- | ---: | ---: |
| 94000 | Terran / Rush / Simple64 | Victory | Defeat | 0.66100 | -0.01894 |
| 94001 | Protoss / Timing / TritonLE | Defeat | Defeat | -0.04501 | -0.06445 |
| 94002 | Zerg / Power / Simple64 | Defeat | Victory | -0.04001 | 0.59277 |
| 94003 | Terran / Macro / TritonLE | Defeat | Tie | -0.06919 | 0.00953 |
| 94004 | Protoss / Air / Simple64 | Victory | Victory | 0.65328 | 0.60123 |
| 94005 | Zerg / Rush / TritonLE | Victory | Victory | 0.64552 | 0.54866 |
| 94006 | Terran / Timing / Simple64 | Defeat | Defeat | -0.04441 | -0.03662 |
| 94007 | Protoss / Power / TritonLE | Defeat | Defeat | -0.02641 | -0.04261 |
| 94008 | Zerg / Macro / Simple64 | Victory | Defeat | 0.71502 | 0.12595 |
| 94009 | Terran / Air / TritonLE | Victory | Victory | 0.69138 | 0.55681 |
| 94010 | Protoss / Rush / Simple64 | Victory | Victory | 0.67340 | 0.59546 |
| 94011 | Zerg / Timing / TritonLE | Victory | Victory | 0.58838 | 0.55222 |

Every first divergence is decision 0: parent SCV to candidate wait, with matching
other recorded fields. This describes broad opening effects, not proof that the
opening change alone causes the outcomes. The failed12-case evaluation stays out
of subsequent fitting and candidate selection.

Complete audit and independent review verify all 15,313 decisions, legal choices,
reward components, finite telescopes, paired returns, first divergences and gate
accounting. Sources, parent/head and optimizer moments remain unchanged; zero
learning updates. A separate frozen wrapper fixes NumPy-Boolean JSON serialization
without changing numerical comparisons. Its regression test reproduces the old
failure and verifies identical corrected gate values. The original auditor and
game inputs remain untouched.

Artifacts: `logs/joint-head-amended-evaluation/` and
`logs/audit/joint-head-amended-evaluation-complete-independent-review.json`.

The actual candidate Zerg Power victory at 94002 is exported as
`logs/replay-proof/joint-head-medium-zerg-win.mp4`:486 H264 frames,960×720,4fps,
121.5 video seconds covering475.71 game seconds with no frame cap. A decoded85-second
frame shows real terrain/buildings/units. Replay rendering uses an omniscient
overview only for viewing; the policy still receives fog-limited observations.
This illustrative win does not override the failed aggregate evaluation.

The ten-second live evaluation sample measures7.13–10.50% whole-machine CPU,
with owned processes on logical CPUs 24–31/nice 10. GPU reads 11%,20.22W,40C;
the learner is CPU-only. This sample is not a total-job peak. Resource receipt:
`logs/audit/joint-head-amended-resource-load.json`.
