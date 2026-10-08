# Actor-relative point scoring experiment

Human imitation remains the current stage; RL is stopped. Astra consultation
identifies missing direct actor-to-cell geometry, alongside severe data scarcity.
Fit03 is the frozen baseline. Add only an opt-in learned point-logit residual
from candidate displacement relative to the selected actor centroid:
[dx,dy,dx squared,dy squared], normalized by32world tiles. Existing terrain
scorer, candidate set, offsets, encoder and losses remain otherwise unchanged.
Use predicted actors in ordinary inference; true actors only in existing
supervision and explicitly labelled oracle diagnostics. This is learned geometry,
not a build-order recipe or candidate restriction. Legacy defaults/checkpoints
must retain their behavior. Empty candidate sets remain valid.

Verify gradients into residual projection and shared argument/encoder, candidate
and entity permutation, coordinate translation of the geometric residual,
checkpoint persistence and exact zero-residual/default parity. Then run one fresh
fit with fit03's sources/seed/50epochs/batch16/rate.001/hidden32/role-pooling,
refinement/actor cutoff/spatial/missing fields,3750updates and600optimizer-second
cap. CPU2threads, no GPU or native games. Bind source/code/checkpoint hashes.

Before fitting, score the baseline point head on every gold point command,
regardless of predicted mode. Report mode accuracy separately. Compare ordinary
and true-ability/actor point errors, within-two-tile accuracy and95th-percentile
error. Gate: at least30% lower oracle mean error, increased within-two-tile
accuracy, no worse95th-percentile error; ordinary complete copying at least24/292;
teaching complete-copy rate no more than five percentage points below fit03.
Harstem is a reused diagnostic, not final acceptance. Preserve failed candidates.
If geometry improves without complete copying, record a limited mechanism result;
next prerequisite is more diverse bounded professional data, not RL or an
optimizer sweep. Dispersed actor groups make centroid geometry imperfect.

Baseline all158gold point commands, frozen fit03 checkpoint e8b4534:
ordinary mean68.1281tiles,p95136.8327,within2tiles0,point-mode correct95;
true-ability/actor mean56.1325tiles,p95126.1687,within2tiles1,mode correct144.
Thus predeclared geometric thresholds are mean<=39.2927tiles,p95<=126.1687,
within2tiles>=2. Complete-copy threshold remains24/292. Baseline teaching487/1190,
so teaching must retain at least428complete commands. This is a development
mechanism gate, not professional competence or native strength acceptance.
Baseline receipt: joint-professional-point-heads-03.json, helper
logs/roadmap/audit_professional_point_heads_01.py binds its bytes and checkpoint.
Five new tests first failed on the absent feature, then passed. Full303tests pass.
Independent read-only review found no gradient, actor-conditioning, metadata or
checkpoint blocker and passed18focused tests. Residual starts at zero without
consuming RNG draws; common initial parameters and first scores remain identical.

Terminal result: fit04 handle8387 exits0;50epochs/3750updates,84.50total seconds.
Source/code/checkpoint bindings verify, checkpoint e86f0735; saved mode reloads.
Teaching459/1190complete; diagnostic11/292complete, so overall gate fails.
All158gold point rows: oracle mean33.6417tiles versus56.1325(40.1%reduction),
p95116.4973versus126.1687,within2tiles4versus1. All three geometric checks pass.
Ordinary mean72.1311versus68.1281;within2tiles1versus0,mode correct88versus95.
This is a limited relational-geometry mechanism result, not competent imitation.
Teaching retention passes428minimum but ordinary24minimum fails. No promotion,
native game or RL update. Preserve both checkpoints. Next prerequisite is more
diverse bounded professional teaching data, not another architecture/optimizer
sweep. Receipts: joint-professional-fit-verification-04.json,
joint-professional-point-heads-04.json and
joint-professional-relative-point-comparison-01.json. All reserved games untouched.
