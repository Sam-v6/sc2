# Condition frozen imitation choices on current engine command candidates

Verified profile opener stalls on2501unavailableTrainSCVrequests. At its first
block, frozen scores assignTrainSCV38%,Smart28%,Barracks15%,Depot5%; no learned
full-game competence is established. Implement optional native command candidates
using engine queries, not a scripted economy rule or narrowed named-action list.

Query all currently observed own actors when a decision is due. Normal commands
use the ordinary resource-aware ability query. Autocast toggle candidates use a
resource-ignored query plus the engine catalog's allow_autocast flag, so energy
or cost exhaustion does not unnecessarily remove toggling. Canonical aliases
share caster availability. The model picks its highest-scored candidate ability,
then an eligible mode and actor group. Point/target validity still requires engine
validation; castability is not a placement or target correctness guarantee.

Default inference, saved weights, supervised objective and raw command grammar
remain unchanged. Explicit flag only forGoalFirst; record query responses and
flag in traces/receipts so independent reconstruction uses the same information.
Preserve unavailable retry guard and actual issued history. No fitting or RL.

Checks: RED then GREEN masks, actor/canonical alias filtering, empty candidate
handling, default parity, autocast with no normal castability, availability protocol
resource flag. Full normal and focused optional tests; independent review. Then
one frozen baseline180game-second opening with the same profile/map/seed/cap32,
120wall seconds and80%wholeCPUguard, CPU-only. Independently reproduce all
choices and inspect actual worker/building appearances and engine errors. No
promotion, extension or strength claim. If the model still chooses inappropriate
legal commands, record that evidence and return to imitation representation/data.
