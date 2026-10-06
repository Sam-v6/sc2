# Explicit native compatibility for partial professional inputs

Assumption: the frozen professional checkpoints expect their partial replay
field-availability convention and generic order IDs. The native opening ablation
shows both corrections are needed for the first SCV prediction. This does not
repair held-game imitation quality or justify RL. Keep both failed fits closed.

Implement one explicit opt-in observation profile for the native adapter. The
profile declares unknown-field categories and catalog-backed specific-to-generic
order IDs. Project model inputs only; preserve full native state in traces, raw
command output, actual model-owned issued history, checkpoint weights and default
behavior. Do not invent missing values or hide any enemies differently. Native
command history is known, so the replay's unknown-command-history declaration
must not erase it. Store the complete profile and its file digest in the receipt.

Checks: a failing unit test first, then input projection non-mutation, equivalent
order IDs, source unknown masks, actual history retention, default parity and
receipt wiring. Existing full tests plus focused Torch tests must pass. Independently
review. Build the profile from the six paired-fit teaching sources only, require their
unknown-field declarations agree and validate each alias against their static
catalogs. No held/reserved labels select the profile. One bounded frozen-baseline
native opener follows, with the same resource guard and immutable checkpoint;
independently reproduce its trace and check actual worker births. No fitting,
policy promotion, full-game acceptance or RL. The complete roadmap stays open.

## Verified implementation and opening result

The opt-in `--observation-profile` is implemented. Projection preserves raw state,
known dispatched history and default behavior. Native startup rejects aliases
absent from the engine remap catalog. Exact loaded profile bytes are hashed and
the receipt records both profile content and digest. The profile is derived from
all rows of the six actually fitted teaching games: declarations agree, and all
740catalog aliases agree; no held/reserved labels select it.

Tests: missing projection first failed, then379normal tests passed (24optional
skips),15focused Torch tests passed, Ruff/diff checks passed. Independent code
and supervisor/verifier reviews found no blockers; suggested provenance checks
and memory-aware actor lookup were applied to the verifier.

Frozen baseline opener30437is terminal exit0; same map/opponent/seed/duration and
cap32as the unprojected inspection. Native observations show three new SCVtags,
worker count12to15and2175final minerals. The model dispatched3TrainSCVand14Smart
commands, all17submitted responsesSuccess. NoDepot/Barracksappeared. It then
repeatedly requestedTrainSCVwhile supply was full:2501unavailable requests were
blocked without changing issued history. These requests are still re-evaluated
from each new state. Do not call this useful full-game imitation or promote the
failed fitted checkpoint. The corrected input contract remedies opening behavior;
macro planning and command targeting remain inadequate.

Whole-host CPU peaked9.7%; noGPU/resource stop/fitting/RL/checkpoint change.
Independent reconstruction reproduces all2518decisions from full native traces
through the recorded profile, including unavailable requests and unchanged issued
history. Evidence: `logs/roadmap/professional-profile-native-01/verification.json`
and bound episode/static/trace/replay/telemetry/policy/profile-source artifacts.
Next work should investigate decisions at the supply-block boundary and preserve
this compatibility fix rather than repeat unchanged full-controller fitting.
