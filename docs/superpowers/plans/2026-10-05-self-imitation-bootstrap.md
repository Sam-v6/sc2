# One bounded self imitation bootstrap

Use only the reviewed 80-game/77,763-transition training archive and its exact
sparse export. Gradient review found value-body norm .015280763 versus actor-body
.000194658, a ratio 78.5 at the retained parent. Fix value loss coefficient .001:
initial weighted value-body norm is 7.85% of actor-body norm. This controls the
starting scale, not every future update or gameplay causality.

One shuffled epoch, seed331, batch256 (304 actual Adam steps), learning rate
.0001, Adam eps1e-5, gradient norm limit .5. Loss is uniform SIL actor plus
.001 times one-sided value loss, with current critic and stopped actor weights.
No PPO replay ratio, advantage centering, entropy bonus, KL penalty, prioritized
sampling, winner-only filter or coefficient search. Copy parent network/context
exactly; start a separately typed `sil-bootstrap` checkpoint with fresh Adam
moments/clocks. Record inherited parent676updates/144episodes separately; offline
model episode/attempt counters stay zero. This is offline RL bootstrap, not
PPO+SIL interleaving or new game training. Preserve parent and all earlier data.

Review source/tests before freezing the fit manifest and launching. Bind reviewed
corpus/gradient source generations, independent receipts, plan, source, settings,
seed and all inputs. Journal every optimizer step and final network/moments;
independent reconstruction must verify the single declared schedule. No resume,
retry fitting or checkpoint selection. A failed fit is retained, never hot-fixed.
After fitting, report full-corpus losses, positive support, parent KL and changed
choices by race. Mean parent-to-candidate training-state KL <=.05 and each race
<=.08 are deployment-to-diagnostic limits; if exceeded do not run games or refit.
These are additional local safeguards, not the SIL paper's acceptance rules.

If the one fit passes integrity/retention, freeze a separate reviewed evaluation
runtime and bank before games. Fresh greedy Hard cases117000–117011 paired parent
and candidate; fresh sampled Easy cases118000–118005 paired with equal policy
seeds. Cases cycle races Terran/Protoss/Zerg, all five builds and both maps by
index modulo3/5/2. Original Terran bot/micro/one-second macro/ordinary combat
reward,1200 game seconds,180 wall seconds. Maximum36 actual games, no replacements
or fitting on these cases. Record partial/failure artifacts. Checkpoint immutability,
seeded actions, terminal rewards, journals and raw replay evidence must be audited.

Support for a later separately declared PPO+SIL continuation requires all active
games audited complete; Hard candidate at least two more wins than parent, mean
discounted-return gain >.02 and nonnegative mean gain in every race; Easy sampled
wins no fewer than parent and mean return no lower by more than .02. Report every
lost parent win/timeout and all outcomes. Failing closes this bootstrap without
extension/promotion; it does not establish that every SIL variant is ineffective.
Passing is development support, not reliable Hard strength or final acceptance.
Reserved50000–50029 stays untouched; Hard is an intermediate step toward higher
computer difficulties. No videos shown before full goal complete. CPU-only with
existing80% ceiling/50% baseline guard,max4engines,8allowed CPUs/nice10. No installs.
