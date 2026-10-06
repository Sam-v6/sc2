# Bounded native stepping during model-chosen waits

The raw imitation runner observes every engine loop even when its learned delay
schedules the next decision several loops ahead. Add opt-in `--max-game-step`
(default1): advance at most this cap and never beyond the scheduled next loop.
A due decision or unavailable unissued action keeps step1. This preserves the
model's requested decision timing and permits rapid control; it is not a
scripted macro action or a new training campaign.

Larger steps change observation cadence: brief intermediate visibility can be
missed, so do not claim general trajectory or fog-memory equivalence. Keep the
existing one-loop default; strength/cadence comparisons remain necessary before
training or evaluation uses a larger cap routinely. The current imitation fits
and their frozen bindings must not change.

Test exact scheduling bounds RED/GREEN; reuse existing issued-history tests.
Record configured cap and selected-step counts in native episode receipt. Run
one15second opening wiring/performance smoke, cap32/seed120601/VeryEasyZerg,
existing failed immutable checkpoint, AcropolisLE. Bound wall60seconds, CPU-only
and80%host guard; no downloads/RL. Compare recorded decision loops/commands to
retained cap1smoke, not outcomes/strength. Confirm replay and immutable weights.

## Verified result

Scheduling test observed missing-helper RED then GREEN. Full normal376test
suite passes with24optional skips;26focused optional-runtime/native adapter
tests pass. Ruff/diff checks pass, and independent review found no blockers.

The cap32native smoke completed14observation callbacks instead of336, with all
11command game loops/raw arguments/delays/action results exactly matching the
retained cap1opening trace. All11decisions and issued-only history were
independently reproduced from the immutable checkpoint. The final observed
own units/player stats and15game-second duration match. A nonempty replay is
saved but not displayed. Wall time was7.856seconds versus9.731previously; this
is one opener under different host contention, not a speed benchmark. Peak
whole-host CPU15.6%includes the concurrently running imitation fit.

No acceptance/cadence default changes:1loop remains the default. Brief vision
between sparse observations can differ in later gameplay. The failed frozen
checkpoint still issuesSmartonly; no model promotion or RL occurred.

- Verification SHA256`5a6aff0bb3f7f046316ddc98a46a630f4f224b74feb735bb79628b82e26556fc`.
