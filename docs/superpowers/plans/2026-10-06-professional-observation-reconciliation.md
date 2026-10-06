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

Timing interpretation resolved with native evidence: all five raw actions in
an existing teaching replay through300loops echo at issue+1; four match original
human SCmdEvents and one is an unmatched engine echo. Historical action
converter attaches them to the preceding observation buffer, explaining stored
professional issue-loop pre-effect states without shifting timestamps. Record
this source contract separately from legacy L-1 extraction. Native build75689,
professional76052engine unavailable; exact producer revision not claimed. Final
phase receipt: issue-loop-phase-verification-01.json. Complete official4.10Linux
package directory confirms no Base76052client; only3.43MiBmetadata downloaded,
no executable/assets. Importer/history/death handling and fitting remain open.


Professional event-history progress: original SCmdEvents now retain one causal
history slot each. Identity-verified commands preserve their exact details and
original unit-target snapshot position; unreconciled events keep only timestamp
and an explicit unknown marker. Unknown slots mask actor/target references and
command-role values rather than inventing actions. The next-action timing label
is withheld when the immediately following original event is unknown. Source
histories require one demonstration row per original event, including same-loop
events; native complete-history burst behavior remains unchanged. Independent
review identified the grouped-row snapshot problem; a failing regression test
confirmed it and the single-event guard fixes it. Fresh suite:283tests pass;
changed Python files pass Ruff.

Local three-game verification is terminal with no optimizer updates:1482verified
commands retain causal event slots;1421currently have representable labels,
1476rows include unknown history and451timing labels are masked. The61target
exclusions are all Smart unit-target commands.60original target positions each
match exactly one currently visible neutral mineral patch (54type665,6type666),
but the converted neutral tag differs from the original command tag. Cached
converter `source/include/observer.hpp` explains this: `updateResourceObs` replaces
resource tags with their first remembered ID when visibility changes. The last
excluded target is a unit seen11loops earlier. Do not drop harvesting capability
or substitute point commands: reconcile source-normalized mineral identities
with explicit provenance, keeping native tags and fog filtering intact. The
remaining remembered-unit target needs a separate legality/representation check.

Evidence: `logs/roadmap/pro-preconverted-probe-01/target-exclusions-audit-01.json`,
`target-exclusions-history-01.json`, `target-exclusions-position-01.json`, and
`logs/roadmap/unittest-event-history-02.log`. These are local representation
checks, not a training-eligible professional corpus or learned competence. The
actual professional importer, own causal deaths/upgrades, source map inputs,
training eligibility and human imitation fit remain open. RL remains stopped.


Actual importer implemented: tournament_import writes native-schema partial
human rows with exact source/map/proof bindings, original commands and causal
neutral-ID/history translations, own tracker deaths/upgrades and dynamic
feature-minimap planes. Height remains explicitly unavailable. Final local
outputs pro-demonstrations-04/{294,774,870}; source-row reader checks recover
1481/1482labels, including all60mineral commands. Known completed upgrades are
preserved while uncertain absences are masked after independent review.
292tests pass. Records still training_eligible=false; separate issue-loop
alignment and partial-source eligibility have not yet been connected to the
trainer. One legitimate remembered enemy target remains excluded by the model
mask and requires native legality evidence. Actual professional fitting is the
next stage; RL remains stopped and the original roadmap remains open.
