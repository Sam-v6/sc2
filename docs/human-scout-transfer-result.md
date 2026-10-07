# Protected worker scouting transfer

The shared human-production executor now uses the baseline's one-time SCV scout.
It selects an idle/mining worker outside pending construction, protects it from
mining and builder selection even when no repeated move order is needed, retreats
at 60% health, and returns to minerals near a complete own base. Own-memory-only
observations preserve ownership without permitting commands to an unobserved actor.

The first native transfer failed its declared gate. Barracks completed later than
in the scripted baseline: the scout departed at 97.5 seconds, so the fixed
135-second return time permitted only 37.5 seconds of travel. At return it was
at (136.4, 65.8), short of enemy spawn (142.5, 33.5). The first real visible enemy
observation was at 248.93 seconds. Orders were accepted and the worker moved;
this was an outing-duration defect, not a stuck movement command. That failed
result and its exact bound sources remain in `human-scout-native-01`.

The revised protocol preserves the initial 75–135-second selection window but
allows at most 60 seconds from selection. Damage can end the outing sooner;
observations containing only remembered ownership cannot restart the deadline.
The frozen `human-scout-native-02` canary uses AcropolisLE, Zerg VeryEasy Rush,
seed816201, 600 game seconds, the unchanged cadence model/prior/profile, CPU-only
execution and the 80% whole-host CPU guard. There is no fit or RL update.

Independent command and replay verification passes the revised scout gate:

- Selected at 97.5 seconds; first actual visible enemy at 138.93 seconds.
- Returned at 139.64 seconds because of damage; subsequently mined at an own base.
- Both scout commands were owned-SCV actions and accepted. No active scout was
  selected by production or had its movement overwritten by harvesting.
- Wall time 48.34 seconds; sampled whole-host CPU peak 5.3%.

The game ended in a cutoff Tie. It produced 33 military births and retained
70 workers, with only one Barracks, one Factory and one Starport. The strict
cadence gate still fails; scouting does not fix the macro policy's capacity deficit.
This result proves this primitive transfer on one native canary, not learned
competence, all-map scouting reliability or completion of the full roadmap.

Regression and integration checks: 498 tests, 32 skipped; named-file Ruff passes.
The timing regression failed before the correction and passed afterwards.
Protocols, replays, traces, source snapshots and independent receipts remain in
`logs/roadmap/human-scout-native-01` and `human-scout-native-02`.
