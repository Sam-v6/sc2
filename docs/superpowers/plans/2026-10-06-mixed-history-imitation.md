# Human replay imitation with imperfect past commands

## Evidence and intended change

The independently verified retained-history trial failed. Teaching complete
commands are1282/4513 with human history but80/4513 with its own predictions;
the reused diagnostic is8/292 and1/292. Frozen input ablation on teaching294
gives124complete commands with32human commands,47with8,25with1 and10with none.
Simply removing history loses useful information. This is evidence of history
sensitivity, not proof that history explains all generalization failures.

Train against the same human next-command labels while sometimes remembering
the model's previous command instead of the human's. Human world states and
decision times remain unchanged. This is supervised imitation, not RL, native
rollout or environment-correct expert relabeling. Invalid hypothetical commands
must not be described as engine-executed actions. The broad action vocabulary,
fog-safe observations and full roadmap remain requirements.

## Implementation checks

- [x] Add causal mixed-history construction. A seeded choice after constructing
  each current input remembers the human command or the current prediction.
  No current/future human label enters current prediction. Empty initial
  history,32command bound, game reset, exclusions and base inputs preserved.
- [x] Prove probability1 matches retained human history and probability0
  matches own prediction history. Prove repeated seeded construction agrees,
  excluded labels still supply past commands, and current/future mutations do
  not change current inputs. Tiny tests establish mechanics only.
- [x] Allow the bounded trainer to refresh teaching examples once per epoch
  through an explicitly supplied provider, keeping one optimizer and original
  wall-clock bound. Run provider under no gradients/eval mode; verify expiry
  before provider/before optimizer update and unchanged sample count.
- [x] Run optional and default tests, Ruff/diff checks, and independent review.

Independent review found a refresh deadline overrun: expired refresh correctly
prevented updates but could finish a whole generation pass beyond the bound.
Ruling: treat this as a required fix before fitting, rather than a deferred
minor, because the user requested bounded CPU work. Supply the original
monotonic deadline to the provider; history generation checks every row and
raises TimeoutError, ending fitting without updates. Tests observed RED then
GREEN. Cost if wrong: fitting may stop early; no extra workload is authorized.

Fourteen optional tests pass; default364tests pass with20optional skips. One
initial default run failed the unrelated descendant-cleanup timing assertion;
the isolated9runtime tests and full rerun pass. No runtime code changed.

## Experiment boundary

Do not launch a fit before implementation checks/review and a frozen contract.
Use only the existing nine teaching games for history generation and labels.
774remains a reused diagnostic;848/51483/51886 remain untouched. Declare the
mixing schedule, seeds, checkpoint source, runtime/bounds and gates before
fitting. Preserve existing failed artifacts. Evaluate using entirely predicted
history, as well as human history, and independently reproduce results.
No RL, native promotion, extension or hyperparameter sweep after a failed trial.
Useful imitation, independent generalization and native competence remain open.

### Frozen next trial settings

One fresh `professional-mixed-history-01/` trial, initialized from the verified
failed retained-history weights, not by extending its output or optimizer.
Same controller/losses. One fresh Adam optimizer at0.0003, batch16,50epochs,
1200seconds including refresh, shuffle8143. Refresh the nine teaching histories
every5epochs using the current policy; human probability0.5 for epochs1–20,
then0 for epochs21–50. Each game resets history; generation seeds are
8150+epoch*100+teaching_game_index. Cached inputs are reused between refreshes.
Provider checks the deadline even when using cache. No diagnostic source enters
this provider. Keep all fourteen previously declared copying/own-history gates
unchanged, including own-teaching complete>=1000/4513. Bind runtime, code,
sources, parent terminal artifacts and schedule before any optimizer update.
Two CPU threads, no CUDA, same80%whole-host guard. All ordinary evaluations
use the final policy's own predictions, rather than cached fitting histories.

These settings are a single supervised experiment, not a guarantee of improved
generalization. Wrapper preflight/review and terminal independent verification
remain to be completed; no fit launched at this implementation milestone.
