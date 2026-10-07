# Learn production commitment order

The count checkpoint `human-production-goals-02` remains frozen. The outcome
completion timing model failed. RL remains off. This experiment teaches which
of two proposed production families the human would issue first; no Depot or
army priorities are inserted by hand.

Use the same 5,378 teaching and 976 previously used development state rows and
repaired original human commands. Per anchor, find each family's next original
issued commitment inside 1008 loops. First command per family only; repeated
attempts do not create quantity labels. Equal-loop commitments are ties and
excluded. A present family precedes an absent family only in a complete uncensored
window. Unresolved potentially relevant production commands censor the window.
Issued intentions, including cancellations, are not labelled successful starts.
Future command events appear only in targets and sampling, never model inputs.

Candidate pairs come from frozen count proposals plus actual next-commitment
families. This target-support union is a training/evaluation sampling rule, not
future-informed live candidate admission. Report proposal-only development
performance separately. Select at most 50,000 teaching base pairs, deterministic
per-game quotas, then mirror their orientations. Weight each game equally and
distinct source-event pairs equally within game so repeated neighboring anchors
do not dominate. One
ExtraTrees classifier:128 trees, leaf4, all features, seed8162, two CPU threads,
fit under600 seconds, watchdog900 seconds and80 percent whole-host CPU. No sweep.
Inputs are masked causal state and two one-hot family identities. Active columns
and all support/baseline statistics come only from teaching data.

Evaluate symmetric probabilities from both pair orientations. Compare against
teaching-only per-pair majority and balanced coin baselines. Require development
accuracy above both, macro family accuracy above pair-majority, and accuracy at
least0.65 on proposed pairs involving buildings. Require at least200 proposal-only
scored pairs; otherwise evidence is insufficient. Report per-game and per-family
results and unknown baseline pairs. Independently reconstruct labels, weights,
predictions and metrics before live use. Offline success does not unlock RL.

If these checks pass, separately implement tested intent lifecycle: unique
unissued ticket per family, immutable admission/expiry, delayed requests survive
zero forecasts, successful observed orders consume tickets, rejected commands
retain the same ticket, no actor overwrite or duplicate starts. Iterate tickets,
not just current positive forecasts. Highest-ranked structurally feasible ticket
reserves resource shortfall before lower-priority choices; missing prerequisite
tickets neither reserve resources nor invent prerequisite production. No
implementation promotion until a frozen same-job native comparison produces
observed workers, Depot, Barracks and sustained army. Then all-race development
panel; broad raw commands, learned combat and eventual RL remain unfinished.
