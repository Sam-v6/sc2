# Hard counterfactual data expansion

Goal: Test whether more varied, directly Hard discovery data supports a useful
reward-driven macro update. The nine Medium pairs did not generalize: the fixed
joint head loses the amended fresh evaluation. Preserve that failure and exclude
its labels and 94000 evaluation outcomes from this experiment. Keep the unchanged
strongest parent, fog-limited live observations and scripted execution/micro;
introduce no macro schedule, opening-action rule or worker quota.

This is one predeclared data-expansion experiment, not an optimizer tournament.
Maximum144 games:32 Hard parent discovery games, up to64 one-action alternatives,
and conditional48 games for24 new matched Hard validation cases. Use the existing
CPU wrapper, four engines maximum and below40% whole-machine CPU; no GPU training,
sudo or installations. Each game:1200 game seconds,180 wall seconds,1-second macro.

Discovery cases97000-97031: cycle Terran/Protoss/Zerg, Rush/Timing/Power/Macro/Air,
and Simple64/TritonLE by index modulo3/5/2. The first30 cover each combination;
the extra two leave race counts11/11/10 and maps16/16. Publish exact assignments
and prove seed banks unplayed before jobs. For each parent trajectory, select
uniformly among its decisions at or before600 game seconds with at least two
legal actions, using default_rng(420000+game_seed). Selection reads time/legal
fields only, never rewards or result. Sample up to two distinct alternatives
uniformly excluding the parent choice, inject each once, then resume the parent's
greedy continuation. Verify exact prefixes and execution; keep unavailable,
failed-to-execute, harmful and neutral cases without replacement. All alternatives
are selected before their outcomes exist.

Before fitting require at least four distinct parent-loss to branch-victory cases
across at least two races, with executed interventions and exact prefix audits.
Report return-order labels separately from victory transitions. No fitting if
this effort gate fails. This is opportunity evidence, not strength acceptance.

Predeclare ONE soft-preference fit now, before collection. Frozen parent body and
critic; augmented output head only. Use all executed paired labels, including
harmful alternatives, weighted by absolute discounted-return difference. Normalize
weights to mean one and average their cross-entropy (equivalently weights summing
one with summed cross-entropy); stop if total weight is zero. Neutral pairs retain
zero weight. Positive difference prefers alternative, negative prefers parent.
Objective: weighted binary cross-entropy +10 parent-to-candidate categorical KL.

Use new discovery-parent states only as anchors; average anchor KL equally across
32 games and then equally across each game's states. Use the same per-state
weights for C=B.T*diag(weights)*B and ridge=.001*trace(C)/65. Symmetric whitening
and fresh Adam(.003,.9,.999,1e-8), maximum256 proposals. Check each proposed head
AFTER conversion against mean anchor KL<=.005; reject the first violation and
retain the preceding feasible head. No greedy-disagreement veto, step-size/ridge
sweep, restart, subset choice or selecting an earlier checkpoint by labels.
Measure initial logits/probability/greedy parity. Report changed decisions,
opening-state KL and SCV/wait margins descriptively; do not impose an opening rule.

The final retained head must choose an actually beneficial loss-to-win alternative
with positive return difference under its full legal mask in at least four distinct
discovery cases spanning two races, meet the fixed KL bound, and preserve body,
critic, moments and parent. Independent fit/source/artifact review before games.
Failure closes the dataset/candidate without switching fitting methods.

If passed, freeze the candidate and validate discovery-independent cases
99000-99023, cycling races/builds/maps by the same rule, parent and candidate each.
All24 assignments precommitted before discovery. Gate: at least three additional
wins, nonlower mean discounted return and positive win gains in at least two races.
Report every regression and paired uncertainty. No fitting against validation,
sample extension or promotion on failure. A pass supports separate independent
confirmation/Hard development, not the final70% Hard acceptance. Reserved50000
acceptance and existing development banks remain untouched by this experiment.

Artifacts: separate ignored logs/hard-counterfactual-data-expansion root. Freeze
source, immutable inputs/maps and case assignments before jobs; retain all traces,
replays and ledger entries. Complete audits and independent review at each gate.
Implementation, tests and input freeze are next; no jobs launched by this plan.
