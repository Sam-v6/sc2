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
