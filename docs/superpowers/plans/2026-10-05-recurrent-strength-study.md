# Controlled recurrent Terran training and fresh strength evaluation

The information diagnostic and actual sequence-PPO backend smoke passed their
independent reviews. This study tests gameplay improvement. Both arms start anew
from the retained parent SHA2560f3e05d9efd5eba4fd238a6282e462599ffc675f008b98fd42925e99f6bb16c6;
no fitted engineering-smoke checkpoint, evaluation trajectory or SIL replay is
an input. Keep the entire parent network frozen and train only the six new
GRU/residual arrays. Macro strategy remains learned, with unchanged ordinary
combat-kills-v1 reward, discount/scaling, masks, macro1-second cadence and
worker/combat execution. No recipes, quotas or attack timing are supplied.

## Fixed training exposure

64 games per arm,128 total, seeds121000–121063 and matching policy seeds. Indexi
uses race(Terran,Protoss,Zerg)[i%3],build(Rush,Timing,Power,Macro,Air)[i%5],
difficulty Medium for eveni/Hard for oddi, map(Simple64,TritonLE)[(i//2)%2].
Thus both difficulties use both maps. Both arms use GRU seed331 and zero residual
heads; control resets hidden state each decision, recurrent resets each episode.
Initial native actions reproduce the retained policy. New Adam moments/clocks
start at zero. Frozen parent arrays never receive gradients.

Collect four cases per arm per round, using one immutable behavior snapshot per
arm for that round. At most four engines; all eight round jobs finish and validate
before either arm learns. Four whole-episode PPO epochs produce16 updates per
arm per round,256 per arm after16 rounds. Settings stay exactly as verified by
the smoke:lr.0003,eps1e-5,clip.2,entropy.01,value.5,gradient limit.5; all contiguous
states reconstruct hidden state from episode start with full BPTT. Advantages
normalize over the four-episode batch, each game has equal minibatch weight.
Game limit1200 seconds,wall180 seconds. No fitting during native games.

No early strength-based stopping, tuning, replacement games or intermediate
checkpoint selection. Preserve every receipt, trajectory, journal, native replay,
fit metric and immutable round checkpoint. Failure or the80% CPU guard stops
owned workers and preserves all known outcomes; incomplete rounds cannot fit.
Source/input errors require a new generation, never hot-edit frozen runs.

## Fresh immutable evaluation

After all training and source/model checks, fixed final policies only:

- Hard greedy: seeds122000–122011,modeevaluate.
- Hard sampled: seeds123000–123011,modesample.
- Easy sampled retention: seeds124000–124005,modesample.

Same race/build cycles; evaluation map usesi%2. All panels pair recurrent,reset
and a typed zero-residual reference equivalent to the retained parent, with
common policy seed equal to game seed. Thirty cases times three roles =90 games,
with original objective/cadence/time limits and no fitting. Declare this complete
bank before training; verify case freshness across all three artifact roots.
Reserved50000–50029 final acceptance cases remain untouched.

For either trained arm to support separate final acceptance, Hard greedy wins
must exceed reference by at least2,mean discounted-return gain>.02,with no
negative per-race mean gain. Sampled Hard wins/mean return cannot fall below
reference; sampled Easy wins cannot fall below reference and mean return gain
must be>=−.02. Report all losses,gains,lost reference wins,time-limit ties and
errors. A failed support gate closes this bounded study without extending or
promoting its models. If both qualify, select by Hard greedy wins,then sampled
Hard wins,then Hard greedy mean return; exact ties prefer the simpler reset arm.
These are development choices,not final reliable-Hard proof.

Attribute extra gameplay benefit to memory only if recurrent qualifies and beats
reset by at least2 wins on each Hard panel,with nonnegative mean return gains on
both. Otherwise report any improvement without claiming memory caused it.

CPU-only learning,one numerical thread,eight-CPU affinity,nice10,maxfour engines,
baseline50%,whole-machine80% guard throughout games and fitting. No sudo/downloads.
Keep native replays unopened; no videos until the overall goal is complete.
Reliable all-race Hard and progression beyond it remain unmet until later
independent gameplay evidence establishes them.
