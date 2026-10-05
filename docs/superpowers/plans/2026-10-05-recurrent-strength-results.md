# Recurrent Terran strength study: training complete, evaluation pending

Reliable all-race Hard strength remains unmet. This is the application of the
literature review's memory and sequence-training mechanism, not a gameplay claim.

The fixed study completed all128native training games:64per arm across Medium
and Hard, three races, five computer builds and two maps. All16rounds completed
without infrastructure failures. Each arm received256whole-episode PPO updates,
with64episodes/attempts, fresh residual optimizer state and a bitwise unchanged
parent network. The final models are recurrent-016.npz and reset-016.npz; neither
is selected or promoted. The unchanged reference is the typed initial reset model.

The controller's128game receipts validate seeded choices, ordinary rewards,
chronological journals, replay headers and typed trajectories. The first batch
passed independent review. Complete independent training review passes all128games,94,846decisions and
32learning calls. The declared90fresh immutable development games are running;
their results remain pending. The reserved50000–50029final
acceptance cases have not been used. Training victories are not acceptance.

The1268two-second whole-machine CPU windows averaged14.47percent and peaked
at31.41percent, below the80percent guard. Learning used no GPU. Keep native
replays unopened; do not render videos until the overall user goal is complete.

Protocol: [fixed study](2026-10-05-recurrent-strength-study.md).
Evidence: logs/recurrent-memory/strength-study/inputs.json,
train-summary.json, train-ledger.json and train-cpu-windows.json;
logs/audit/recurrent-strength-implementation-review.json and
recurrent-strength-first-batch-independent-review.json, and
recurrent-strength-training-independent-review.json.
