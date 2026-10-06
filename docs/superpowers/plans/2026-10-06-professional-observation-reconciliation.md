# Professional replay observation reconciliation

Use the existing `Sam-v6/terran-rl` worktree. Current work is supervised human imitation; keep RL stopped until a competent imitation policy is demonstrated. Preserve reserved human games and all prior evidence.

Assumption: public preconverted player observations can be reconciled with original professional replay commands, avoiding the missing Linux client version. Test that assumption before adding these records to training. The converter omits command details and some observations; do not fabricate them or redefine the final sensory/action scope.

- [x] Obtain publisher metadata and bounded original Clem replay samples, verify checksums and player identities.
- [x] Correct Windows database offset width, retrieve three independently compressed candidate records inside16MiB contract, and decode header/scalar/image/action blocks.
- [x] Compare exact original command loops and truncated targets; preserve unresolved cases. Found2181/2229 unique matches; no conflicting ability mappings in these matches.
- [ ] Independently verify ability mappings and selected actor tags using official replay events/native catalog evidence.
- [ ] Decode unit blocks with schema/bounds verification. Confirm pre-command observations and player fog visibility using concrete records and converter source.
- [ ] Restore original queue flags/point precision only for verified commands. Mask/exclude unavailable observations and unknown action modes explicitly. Recover upgrades from player-visible replay events if feasible.
- [ ] Build an importer with meaningful fixture tests, source receipts and compatibility checks against native inference. Do not mix partial records silently into existing datasets.
- [ ] Assemble professional teaching/validation splits by whole game and evaluate imitation before further frozen native tests. Larger corpus downloads require a concrete bounded size decision within user constraints.
- [ ] Demonstrate competent human imitation before RL; continue full sensory/action coverage, learned micro transfer and the original all-race Hard/higher-difficulty acceptance requirements.

Evidence: `logs/roadmap/pro-preconverted-probe-01/`. No model fitting, native match, optimizer or RL ran during the compatibility probe. No full tournament archive/database or pending legacy-client download was retrieved.
