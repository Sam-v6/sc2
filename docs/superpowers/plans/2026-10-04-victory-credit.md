# Stronger victory credit from the retained learned policy

The concentrated-sampling gate failed: temperature 1 scored 0/30 and temperature
0.5 scored 1/30 on matched frozen sampled Hard cases. Do not train that branch.
The retained greedy kills-only Easy40 policy remains best at 12/30.

On the retained Hard40 training run, mean discounted external kill return from
the starting state was 0.097 versus 0.00983 for the victory payoff. On Easy40,
these were 0.180 and 0.0365. Victories were rare (2/40 Hard, 8/40 Easy), and late
payoffs are discounted. The Hard mean includes 38 zero-payoff games; on the
two winning games, mean victory credit was 0.1966. These averages reflect both
sparsity and weighting, and do not prove proxy optimization caused
the regression, but motivate putting more weight on the requested outcome.
Receipt: `logs/audit/hard-credit-signal-profile.json`.

## One-factor protocol

1. Copy the original kills-only source, preserving all gameplay, observations,
   actions, discount, potential, killed-value credit, reward scale, optimizer,
   starting arrays and RNG. Change only raw Victory payoff 100 to 1000, with
   declared reward context `combat-kills-victory-v1`. Defeats and horizon ties
   keep zero outcome payoff. Do not reset the critic or add temperature changes.
2. Verify callback win/loss/tie targets and the full suite, then perform an
   explicit metadata-only objective migration. Numerical arrays and all other
   metadata must be exact; no pending rollout can cross contexts.
3. Replay the known frozen Hard Protoss Air seed20013 case in real SC2. Check
   Victory, unchanged initial bytes, identical original gameplay trace and
   only the expected terminal reward difference. This is capability/context
   validation on a reused winning case, not new learned strength.
4. Verify separate two-game train/resume smoke checks, cadence and optimizer
   chaining. Start the real bounded Hard40 continuation from the untouched
   migrated initial, using the same opponent schedule/seed base30000 and four
   workers as the retained old Hard40 control. Preserve per-batch checkpoints,
   replay/action receipts and source hashes. The larger target can alter critic
   gradients as part of this reward intervention; monitor returns/finite state.
5. Freeze the final checkpoint and evaluate the same all-race/five-build/two-map
   greedy Hard30 development cases, seed20000, 1200 game seconds/300 wall seconds.
   Compare actual outcomes against the parent12/30 and old Hard40 final8/30.
   Keep the best parent and untouched fresh acceptance bank. A reward change,
   successful fixture or successful update is not Hard acceptance.

## Current verification

The stronger endpoint test failed before implementation, then the isolated
source passed all 80 tests, including Torch update/resume integration. Only
`src/rl/terran.py` differs from the original source (reward name and win payoff).
Source archive: `logs/audit/ppo-victory-credit-source`.

Migration preserves every numeric payload and every other metadata field.
Immutable initial SHA-256:
7a7d3816df944d39a297b0b5d3ec4d7808f68cebb57b58928bcbb0342d063bd4.
Receipt: `logs/ppo-victory-credit/migration.json`. The real frozen winning-case
check completed with Victory and unchanged bytes. All 406 decisions match the
parent exactly except the terminal raw payoff 100->1000 and scaled reward +9.
Receipt: `logs/audit/victory-credit-frozen-win-results.json`.

Separate two-game 120-second train/resume checks completed with zero failures
and four horizon ties. Resume advanced the optimizer 676->684 updates, retained
cadence 1 and chained checkpoints correctly. Initial/canonical experiment
policies remained untouched by these smokes. Receipt:
`logs/audit/victory-credit-smoke-results.json`. Independent review confirmed
80 tests and exact context migration; larger critic errors/gradient influence
are an experimental risk, not arithmetic overflow.

The Hard40 continuation completed with 3 wins, 34 losses, 3 horizon ties and
zero failures. All 27,965 transition rewards and per-state returns passed the
audit (maximum return error 2.84e-14). All numerical checkpoint payloads are
finite; sources differ from the matched old control only in `src/rl/terran.py`.
Receipt: `logs/audit/victory-credit-hard-1-results.json`. The final has 184
episodes/attempts and 1136 updates. Preserved SHA-256:
7e4a171ae602490d33e22e35ce8ede52fd26b7eca648828b2723225c3e738b10.
Its separate frozen Hard30 evaluation completed with 0 wins, 27 losses,
3 horizon ties and zero failures. Checkpoint bytes stayed unchanged; all
20,238 reward components and per-state returns passed (maximum return error
3.50e-15). It regressed against the parent 12/30 and old Hard40 final 8/30;
do not promote. Receipt: `logs/audit/victory-credit-final-evaluate-hard30-results.json`.
Production source remains unchanged.

Through the first winning collection batch, all 16 games matched the old control
exactly in numerical behavior state and gameplay, except the intended +9 scaled
terminal payoff on the victory. Subsequent optimizer behavior can diverge.
Receipt: `logs/audit/victory-credit-first-winning-batch-parity.json`.

A read-only full-batch gradient diagnostic on the retained first winning batch
shows value MSE 0.205->9.986 under the stronger payoff. Policy body gradient norm
was 0.0142->0.0151, while weighted critic body gradient was 0.191->1.337. Actual
training uses shuffled minibatches, Adam and clipping; this does not establish
actual update magnitude, instability or strength. It documents possible shared
representation interference for further investigation. Receipt:
`logs/audit/victory-credit-gradient-results.json`.

A real post-update Hard Zerg Air training victory (seed 30164) is exported to
`logs/replay-proof/victory-credit-hard-zerg-training-win.mp4`: all 841.70 game
seconds, 858 frames at 960x720/4fps, 214.5 seconds of video, no frame cutoff.
The game receipt confirms Victory; the export receipt confirms rendering. A
late frame was inspected. This training victory does not override the failed
frozen evaluation.
