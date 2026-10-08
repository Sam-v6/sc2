# Human production forecast diagnostic: verified result

RL remains disabled. The two fixed ridge diagnostics completed normally, using 2 CPU threads and peaking at 8.7 percent whole-host CPU. All 3,162 labels independently reconstruct from original event chronology and unresolved-event censorship; all 6,324 predictions independently reconstruct through an equivalent primal affine model. The ordinary suite passes 399 tests with 31 optional skips; focused checks, Ruff and diff checks pass.

Six repaired teaching games yield 2,436 forecast rows referring to 996 unique production events. Three previously used development games yield 726 rows referring to 262 events. Repeated rows are not additional independent demonstrations. Reserved games remain untouched. Future commands are targets only; inputs remain masked current observations and causal prior history. This is an offline diagnostic, not a controller.

| Development metric | Majority/mean baseline | Current state | State and human history |
|---|---:|---:|---:|
| Ability accuracy | 37.47% | 34.30% | 30.44% |
| Equal-weight class recall | 5.56% | 12.01% | 11.30% |
| Nonworker accuracy | 0% | 15.86% | 16.08% |
| Positive-delay accuracy | 36.21% | 33.62% | 26.29% |
| Delay MAE | 1.69s | 1.72s | 1.99s |

Current state fits 69.29% of teaching choices, versus 97.54% with history. The large teaching/development gap is evidence of poor generalization, especially with history. It does not prove that all state-based approaches fail. Current-state development predictions copy 21/28 expansions, 38/217 Marines, 6/44 Depots and 0/13 Barracks. The solved-system residuals are 7.45e-15 and 5.89e-15, removing the earlier optimization-convergence ambiguity but establishing no native competence.

Close both fixed diagnostics. No budget extension, native promotion or RL. Next test one nonlinear current-state model because a linear score cannot directly express resource/count thresholds and their interactions. Keep the same source split and report the same rare-class/positive-delay metrics; no history retry or hyperparameter sweep. This tests model form before committing to a controller redesign. If it fails, prioritize source coverage/observation sufficiency rather than repeating full-controller fits.

Artifacts: `logs/roadmap/production-forecast-probe-01/`; runner and independent verifier live in `logs/roadmap/`. Report SHA256 `eac735dd377a3308e962bebe8dcddb19881820bd181e9fd11f56e56499cbf6c0`. Verification receipt binds the report. Full raw control, learned micro, native imitation, Hard wins and higher difficulties remain unachieved.

A separate final check also reconstructs every3,162stored causal feature row exactly
from the bound source corpus; see`feature-verification.json`.
