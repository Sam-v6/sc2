# Stronger victory credit from the retained learned policy

The concentrated-sampling gate failed: temperature 1 scored 0/30 and temperature
0.5 scored 1/30 on matched frozen sampled Hard cases. Do not train that branch.
The retained greedy kills-only Easy40 policy remains best at 12/30.

On the retained Hard40 training run, mean discounted external kill return from
the starting state was 0.097 versus 0.00983 for the victory payoff. On Easy40,
these were 0.180 and 0.0365. Victories were rare (2/40 Hard, 8/40 Easy), and late
payoffs are discounted. The Hard mean includes38 zero-payoff games; on the
two winning games, mean victory credit was0.1966. These averages reflect both
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
source passed all80 tests, including Torch update/resume integration. Only
`src/rl/terran.py` differs from the original source (reward name and win payoff).
Source archive: `logs/audit/ppo-victory-credit-source`.

Migration preserves every numeric payload and every other metadata field.
Immutable initial SHA-256:
7a7d3816df944d39a297b0b5d3ec4d7808f68cebb57b58928bcbb0342d063bd4.
Receipt: `logs/ppo-victory-credit/migration.json`. The real frozen winning-case
check completed with Victory and unchanged bytes. All406 decisions match the
parent exactly except the terminal raw payoff100->1000 and scaled reward+9.
Receipt: `logs/audit/victory-credit-frozen-win-results.json`.

Separate two-game120-second train/resume checks completed with zero failures
and four horizon ties. Resume advanced the optimizer676->684 updates, retained
cadence1 and chained checkpoints correctly. Initial/canonical experiment
policies remained untouched by these smokes. Receipt:
`logs/audit/victory-credit-smoke-results.json`. Independent review confirmed
80 tests and exact context migration; larger critic errors/gradient influence
are an experimental risk, not arithmetic overflow.

The untouched initial Hard40 continuation is now running with four workers.
Production source remains unchanged.
