# Human production imitation through verified primitives

The scripted Terran baseline is verified at 30/30 fresh Hard wins. This experiment
reconnects human-selected production to its execution primitives. It is an
intermediate macro experiment; full command imitation, learned attack decisions,
micro transfer and RL remain requirements. RL is off throughout this experiment.

Use only the repaired 11 teaching and three previously used development games
under `logs/roadmap/human-visibility-reimport-01/corpus`. Keep reserved games
untouched and verify the corpus receipt and reader bindings before preparation.
Labels are simultaneous original own production outcomes in the next 1,008 game
loops; independently reconstruct them from original tracker events. Do not use
future outcomes as inputs. Preserve complete-window exclusions and all coverage.

Keep the prior model budget: ExtraTrees 128 trees, minimum leaf four, all active
teaching columns, seed 8160, two CPU threads, teaching standard-deviation scaling
with floor 0.1. Compare against zero and teaching-mean predictions. No architecture,
threshold or training-budget sweep. Require lower development MAE and higher
macro F1 than both baselines, building and military precision/recall at least 25
percent, and no unsupported development family. Reconstruct checkpoint predictions
and labels independently before native play. This pass is offline evidence only.

The intervention is repaired observations plus verified execution: mining/cargo
protection, interrupted construction, reachability/clearance, depot lowering,
MULEs and per-unit combat between forecasts. Learned requests own their casters;
assistance cannot introduce worker/army/structure production choices. Defer an
unaffordable request without blocking affordable learned requests. Trace forecast
and micro phases separately, with learned execution and scripted assistance.

Attack timing, destinations, gas quotas, worker selection, physical placement
and combat micro are declared scripted assists. A win here cannot be called full
strategy imitation. Broader raw controls remain available in the roadmap; the
production forecast does not replace them or unlock RL by itself.

After engineering tests and verified offline passing, run one bounded native
canary, then freeze a six-game all-race Rush/Macro development panel. Record exact
model/source hashes, original replays, production chronology, requests/acknowledgments,
errors, ownership and sampled fog. Compare matched execution before fresh learned
acceptance. Diagnose failures instead of extending an unchanged fit.

Use the existing local ML runtime, GPU disabled, two threads, and a whole-host
80 percent guard with three consecutive high samples. Cap preparation/verification
at 900 wall seconds and optimizer at 600 seconds. No sudo or new dependencies.
