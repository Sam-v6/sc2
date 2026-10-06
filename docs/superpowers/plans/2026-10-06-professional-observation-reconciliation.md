# Professional replay observation reconciliation

Use the existing `Sam-v6/terran-rl` worktree. Current work is supervised human imitation; keep RL stopped until a competent imitation policy is demonstrated. Preserve reserved human games and all prior evidence.

Assumption: public preconverted player observations can be reconciled with original professional replay commands, avoiding the missing Linux client version. Test that assumption before adding these records to training. The converter omits command details and some observations; do not fabricate them or redefine the final sensory/action scope.

- [x] Obtain publisher metadata and bounded original Clem replay samples, verify checksums and player identities.
- [x] Correct Windows database offset width, retrieve three independently compressed candidate records inside16MiB contract, and decode header/scalar/image/action blocks.
- [x] Compare exact original command loops and truncated targets; preserve unresolved cases. Found2181/2229 unique matches; no conflicting ability mappings in these matches.
- [ ] Independently verify ability mappings and selected actor tags using official replay events/native catalog evidence.
- [x] Decode complete unit/neutral blocks with schema/bounds verification and exact byte consumption. All3543converted commands use present Self actors; first TrainSCV observations retain50minerals and empty CommandCenter orders.
- [ ] Confirm later pre-command observations and player fog visibility. Resolve visibility-grid coordinates before importing.
- [x] Correct packed selection-mask interpretation and corroborate all1027matched commands across Future/BackupI and Harstem games; retain2034corroborated actor groups total.
- [ ] Resolve or explicitly exclude remaining39Scarlett selection disagreements and108unknown selections; verify mixed subgroup dispatch.
- [x] Retrieve exact original map archives by replay cache hash inside16MiBbudget and verify dimensions. Correct two stale converted map headers.
- [ ] Apply verified world-coordinate flip/uniform-scale geometry and confirm residual unit-footprint visibility cases.
- [ ] Restore original queue flags/point precision only for verified commands. Mask/exclude unavailable observations and unknown action modes explicitly. Recover upgrades from player-visible replay events if feasible.
- [x] Implement tested bounded tournament wire decoder; independently review it and reproduce all3543converted commands across three real records. Full252tests pass.
- [x] Locate14player-owned completed upgrades with exact native catalog names; exclude opponent tracker upgrades and retain unknown names.
- [x] Project all3542professional observations through the native fog filter; preserve explicit unknowns and reject partial states in the legacy encoder. Upstream energy/capacity bug is confirmed and current energy masked;256tests pass.
- [ ] Extend model inputs with explicit missing-field features and source-grid geometry; preserve old checkpoint/native behavior by default.
- [ ] Build native demonstration importer with command/actor/ability reconciliation, exact-map geometry, causal own upgrades/deaths/history and explicit missing-field masks; verify native inference compatibility. Do not mix partial records silently into existing datasets.
- [ ] Assemble professional teaching/validation splits by whole game and evaluate imitation before further frozen native tests. Larger corpus downloads require a concrete bounded size decision within user constraints.
- [ ] Demonstrate competent human imitation before RL; continue full sensory/action coverage, learned micro transfer and the original all-race Hard/higher-difficulty acceptance requirements.

Evidence: `logs/roadmap/pro-preconverted-probe-01/`. No model fitting, native match, optimizer or RL ran during the compatibility probe. No full tournament archive/database or pending legacy-client download was retrieved.

Missing-field step progress: opt-in entity/scene availability features implemented
and tested; default legacy input format preserved. Trainer/checkpoint/native-agent
configuration and coarse-grid geometry remain open, so the step above remains
unchecked. No professional fitting or RL started.

Missing-field integration progress: trainer flag/checkpoint metadata/native
inference now share the format; source geometry and plane availability accompany
spatial patches.270tests and36professional-state format probes pass. Original
map height reconciliation and command chronology/labels remain open. The full
importer and professional fitting are still not completed; no RL restarted.

Command reconciliation progress: tested identity helper now combines original
selection, independent name/index, exact loop and target, supported flags and
mutual uniqueness; restores queue and point precision.1482commands verified,
747excluded in final receipt03. Unknown events retain possible identities to
block ambiguous reuse.277tests pass and independent review confirms fixes.
159worker-training examples support pre-effect phase, but full chronology and
version-specific mappings remain open; these records are still not training
eligible. No guessed loop offsets or invented complete history have been added.
