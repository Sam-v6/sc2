# Matched production-state learning comparison

Goal: test whether the verified public-production inputs improve learned macro play over both unchanged parent and matched old-observation training. Information-gate passage alone is insufficient; reliable Hard remains unmet.

Prerequisite: exact3183decision telemetry parity and independently reconstructed10.4369percent held-out Brier improvement from production-state-observations plan. Starport remains unexposed and diagnostic support is narrow.

Two isolated frozen archives:

- Control retains5460features; snapshot includes the transparent production telemetry but encoder ignores it.
- Sensory appends35scaled public-production inputs to5495features. All27actions, masks, micro, executor, objective, one-second cadence/gamma, PPOsettings and shared body/value architecture match control. Use the original verified main PPO context, not new exploration/reward/stance changes.
- Copy retained0f3checkpoint for control; append35zero rows to actor first-layer weights and its Adam moments for sensory. All old arrays, logits/values/greedy choices, RNG, counters/reward/backend/settings remain exact within verified floating precision. Distinct feature schema rejects cross-loading. Never initialize from smoke-updated weights.

Before learning, verify encoder/prefix/callback transition shapes and frozen original-output parity. Run separate cloned train2/resume2/frozen2smokes per arm, VeryEasy120game/180wall seconds: trainingbase87000(actual87144–87147given144priorattempts), frozen87200–87201. No smoke evidence is strength evidence. Preserve failures and original source versions; actual-learning inputs freeze only after verified smoke.

Predeclare40Mediumtraining games per arm, fourworkers/batch, base seed88000with preserved144attempt offset -> actual88144–88183. Case schedule follows original trainer: racesTerran/Protoss/Zerg, buildsRush/Timing/Power/Macro/Air, mapsSimple64/TritonLE, using original episode-index144–183rotation. Control/sensory match exact cases, initial old arrays and budgets. No source edits during jobs, selective reruns or extensions.

Frozen development comparison:30Mediumcases89000–89029 for unchanged parent, control40 and sensory40; ten/race, bothmaps/allfivebuilds. Same greedy mode, original cadence/executor/micro/objective. Compare complete matched schedules; source/checkpoint bytes immutable throughout. This is a new development bank, not final Hard acceptance. No test bank outcomes inform training or context choices.

Sensory progress gate: at least3more victories than BOTH parent and control, plus mean existing-objective discounted return no lower than either. This small development threshold permits a separately declared Hard comparison, not a strength/generalization claim. Report actual production-state exposure and commands/completed units, not issuance alone. Stop without promotion or extension if gate fails, insufficient cases complete, or audit fails. ReservedHardbank50000 and original14/13development effort gates remain unchanged.

Audit all rollouts/masks/reward/terminal context/returns, complete schedules, source/behavior/checkpoint hashes, finite optimizer state and exact counters; reconstruct every actual frozen greedy decision. Independent review required. Full raw order data is not recorded, so aggregate-consistency claims retain that limitation.

No sudo/downloads; eightCPUs/nice+10/BLAS1/softwareGL/CPU-only, maxfourtotalSC2games. Use existing siblingTorch interpreter with absolute(non-resolved)path and Python-B. All sources/artifacts stay in owned worktree; preserve maindefault/retained model until strength evidence supports change.

## Implementation and smoke ledger

Control archive uses the already verified observation-only ProductionProbe while preserving old encoder. Sensory archive adds sensory_terran.py with35inputs and two original callback bodies using extended encoding. All masks, primitives, combat micro, potential and finite terminal objective remain inherited. The learner/update helper supports dynamic checkpoint dimensions unchanged.

Three sensory tests fail on missing module first, then pass. Full suites85control/88sensory pass. Initial archive omitted config/plot.yaml and both full suites failed plotting; copied original config only and retained failed outputs. No plotting code changes.

Control initial bytes match retained0f3. Sensory initial3232e40ff4a3ee3b04c2d6f45af59f8ca53a76e8d6beb0458bab5c5fe4af6eaf appends zero rows and extends schema/empty states only. All old network and optimizer arrays, RNG, settings, counters and other metadata match. Across3183probe states, logits/values/probabilities differ by at most2.22e-16 with identical masked greedy choices. Independent reviewer reconstructs migration/parity and checks inherited execution/reward scope; no material blocker.

All12actual smoke games complete without infrastructure/learner failures. Each arm runs train2/resume2/frozen2 at declared seeds; each phase224decisions. Episodes/attempts144to148 and updates676to680to684; final frozen checkpoint unchanged. Smoke weights separate from original actual-learning inputs. Initial reporting harness looked for summary.json but trainer writes run-id.summary.json: first control train2 completed; preserved original harness and harvested that phase without repeating games before continuing v2. Audit verifies schedules, counters, replaybytes, terminal context and finite states. logs/[arm]/smoke/audit.json.

Ten-second active smoke host sample3.14to11.11percentCPU; all owned processes pinned24–31 and nice10; GPU13percent/19.55W/40C with learnerCUDAhidden. logs/audit/production-sensory-smoke-v2-resource-load.json. Short host sample does not guarantee unrelated workloads stay below limit.

Original actual-learning inputs and exact schedules frozen in logs/audit/production-sensory-learning-inputs.json; driver and archive/config hashes retained. Four workers maximum, sequential phases. No matched learning or new bank games completed at this ledger update.


## Live matched-run ledger

Independent reviewer reconstructs both smoke audits and checks exact cases, input/source/driver hashes, preserved original learning weights, sequential four-worker phases and frozen-phase checks. No material launch blocker. Matched driver started through quiet wrapper; live handle64350. First four-game host sample13.3696to13.6258percentCPU, owned24–31/nice10; GPU13percent/20W/40C. logs/audit/production-sensory-learning-resource-load.json.

Control has16of40 completed training receipts at this update, zero infrastructure/learner failures, updates908. Outcome comparison remains pending. Four audit tests pass, including rejecting incorrect terminal credit, broken combat-score continuity and wrong next potential. First actual four-game control batch3898states reconstructs every sampled choice from recorded behavior/policy_seed and reward/component/telescoped discounted returns. logs/audit/production-sensory-firstbatch-audit.json. Scope is first batch only; complete experiment audit and independent review still required. No source/checkpoint edits during the live run; no Hard promotion evidence.


Independent audit review found two evidence holes, not observed runtime failures: checkpoint identity lacked initial/prior-promoted links and batch sample/update counts were lower bounds. Six additional regressions fail before helper implementation, then ten total audit tests pass. Helpers now require exact transitionsum, epochs*ceil(samples/batch_size) optimizer increments, consistent batch metrics, declared initial-to-promoted-to-next behavior, and intended parent/final evaluation hashes/updates. Reviewer independently confirms all ten tests and first real batch0f3toea531updates676to740. No material remaining defect found in these fixes; full-phase audit still pending.

Completed control prefix28games/24014states, seven batches; chained behavior hashes and exact optimizer increments verify through1064updates, zero recorded failures. logs/audit/production-sensory-prefix-chain-audit.json. This prefix supplies collection/accounting evidence only; no matched strength result. Live experiment handle64350 remains running.


## Completed control training phase

Control40 finishes4Victory/29Defeat/7Tie, zero failures. Full training-phase audit and independent read-only reconstruction pass35727sampled decisions, source/case/checkpoint history, exact transition totals and optimizer increments, all reward/terminal components and discounted telescoping. Episodes/attempts184, updates1252; mean discounted training return.11506899874374181. logs/ppo-production-control/partial-learning-audit.json. File remains explicitly partial because frozen evaluations are pending.

Logged control production exposure includes17719townhall/19987Barracks/5397Factory/213Starport queue states and13461pending-supply states. Starport now has actual training exposure; the original held-out information diagnostic still supplied no Starport-specific predictive validation. Observed maximum45Marines/6Marauders/2Tanks/5Medivacs is a snapshot maximum, not cumulative completed production.

Sequential driver advances to sensory-train40, live handle64350. Comparator is independently checked: both full nonpartial audits, allfivephases, exact30case matched bank and original3win/return gates required. No matched strength verdict until all frozen evaluations and full audits finish.


## Actual starting-behavior parity and sensory update path

First four sensory training games exactly match corresponding control games88144–88147: same policy seeds, outcomes, durations, rewards, and byte-identical full action/snapshot/mask/execution/component traces across3898decisions. logs/audit/production-sensory-firstbatch-parity.json. Scope is the original-behavior batch before updates; subsequent learning is expected to diverge.

Frozen sensory behavior checkpoint after first update af0804593085a06182fdc481f35d6d94ae93990ddaa2c3c48e3fcf9dfca051f0 has148episodes/attempts and740updates.24of35 appended input rows acquire nonzero weights, with finite nonzero Adam moments/variances, weightL2.6633706529635178. The other11rows were unexposed in this batch. logs/audit/production-sensory-first-update-inputs.json. This verifies that added inputs reach the optimizer; no strength claim. Sensory phase remains live; full evaluation/audits pending.


## Completed sensory training and parent evaluation

Sensory40 finishes3Victory/33Defeat/4Tie, zero failures. Complete training-phase audit and independent reconstruction pass34040decisions, all sampled choices, source/case/behavior history, exact optimizer/sample counts, reward components and finite terminal telescoping. Mean discounted training return.06378040684608147; episodes/attempts184, updates1236. Logged queue-state exposure16810townhall/19325Barracks/5249Factory/719Starport and12826pending-supply states. This supplies training-path evidence, not improved playing strength.

Named byte-exact final training snapshots preserved: control6f54391915f5c46bd15b9038cff67c4108da895bcef5ef176968f80511ab9576; sensorya7f7ba8b306f80ef3313658285f2601035d51ef51aa73ea6d4f22b0152e599dc. logs/[arm]/frozen-medium40.npz and logs/audit/production-sensory-final-training-snapshots.json. Driver continues evaluating its unchanged learning.npz files as predeclared; these copies do not alter jobs.

Unchanged parent frozenMedium30 finishes22Victory/8Defeat, zero failures and exact checkpoint preservation. Independent full-phase audit verifies15293greedy decisions and rewards, mean discounted return.463629449028912; winsTerran8/10,Protoss5/10,Zerg9/10. Bank89000–89029 is fresh Medium development, not final Hard acceptance. The declared sensory gate now implies at least25wins and return no lower than this parent, as well as its original control-relative requirements. No thresholds changed. Trained control/sensory frozen evaluations remain pending; livehandle64350 verified active.


## Closed matched comparison

All170games finish with zero failures; driver64350 exits0. Complete nonpartial audits and independent reconstruction verify allfivephases, original cases/source/model history, optimizer increments, frozen decisions/rewards and unchanged evaluation checkpoint bytes. Frozen Medium bank89000–89029: parent22Victory/8Defeat, return.463629449028912; control21Victory/9Defeat, return.4394904949697444; sensory6Victory/24Defeat, return.06311688742752371. Sensory frozen audit reconstructs18634decisions. Allfourpredeclared win/return gate checks fail. No extension, promotion or conditionalHardcomparison. Retained original0f3 and maindefault remain unchanged; reliableHardgoal remains unmet.

logs/audit/production-sensory-comparison.json retains complete matched outcomes and audit/input hashes. Both full audits independently reproduce; reviewer finds no material evidence defect. Useful next-state prediction did not translate into improved gameplay here. The result does not establish that production information is generally harmful or identify the responsible learning mechanism.

Firstseed where bothparent/controlwin but sensoryloses is89011,ZergMacro,Simple64. Originalparent maximumarmy48/32Marines; control52/39; sensory0/0, losing at638.93game seconds. Selected by explicit post-audit diagnostic rule, not strength evidence. logs/audit/production-sensory-regression-case.json. Full replay exports started after every training/evaluation process was terminal; at mosttwoquietreplayengines.

Under conditionaluserpermission, Astra reviews the failed learning arm and identifies a concrete optimizer confound: appendedzero-moment rows inherit globalAdam age676. For identical gradient histories, ignoringepsilon, inherited-clock/fresh-clock step-magnitude ratios are2.218atlocal1,3.823at4,4.634at12,3.557at40. These ratios are analytic bias corrections, not measured latent movement or proven failure causes. Astra recommends a fixed-firstbatch2x2offline replay separating new-row Adamage and critic gradient into newrows, plus original-input control. Require factual sensory/control update reproduction first, and quantify actor/KL/wait/value/gradient/movement on fixed training and separate probe states. Defer bootstrapped-credit work until this migration/learning-dynamics diagnostic is resolved. No additionalgames or architecture promotion authorized by this diagnostic alone.


Both matched replay exports finish successfully; handles16535/25001 exit0. Regression652frames/163video seconds/all639.29game seconds; originalparent472frames/118video seconds/all462.5game seconds. H264960x720/4fps, overview/omniscient playback only, no frame-limit truncation. ffprobe verifies streams/counts/durations; extracted QA stills visually inspected. logs/replay-proof/production-sensory-medium-zerg-regression.mp4 and production-parent-medium-zerg-win.mp4, with frames/export receipts. No interactiveWindows validation claimed. The regression video is queued in the Codex panel.

Next offline diagnostic separately predeclared in [fixed-update replay](2026-10-05-production-input-update-replay.md). No optimizer replays or new game-training arm yet.
