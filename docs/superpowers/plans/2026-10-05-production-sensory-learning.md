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
