# Human worker queues and native supply stalls

October 7, 2026. This diagnosis uses the winning professional source game870 and
fixed-plan native20–22. These are fixed human macro commands with scripted mining
and combat assistance against VeryEasy, with forced diagnostic exits. They are
not learned victories. Imitation fitting and RL remain paused.

## What is actually happening

Replay tracker events through the exclusive cutoff9224 show55 SCV births in the
source and45 in native20,21 and22. Neither source nor native20 lost an SCV before
that cutoff. Raw unit snapshots omit some living workers, including workers inside
refineries; earlier counts41/50 described visible snapshot entries, not total
living SCVs. Tracker births and player worker totals are the appropriate evidence.

At loop6000, source and native22 both have33 workers,21 army supply and62 supply
capacity. By8800, the source snapshot has49 workers and25 army supply; native22
has45 workers and40 army supply. Capacity is85 in both. Near9216, the source has
54 workers and29 army supply; native has45 workers and45 army supply, with93
capacity in both. Source sample loops are retained in the audit rather than
pretending irregular source observations were taken at exact native times.

Native22 has159.29 **combined producer-seconds** with a zero-progress SCV at the
head of a Command Center queue and full supply, confirmed in consecutive native
samples. This adds simultaneous stalls across Command Centers, not elapsed game
time. Main-base stalls include6656–7688 and8504–9104. At8800 its main queue contains
five SCVs, all at zero progress. The second base has three, also at zero progress.

The source lost ten Hellions before9224; native20 lost none. Native army retention
and delayed execution change resource and supply requirements. The human's exact
supply timestamps therefore cannot serve as an adaptive production strategy.
This evidence does not attribute all ten missing births to one cause: construction,
resource timing, cancellations and source queue truncation also matter.

## Corrected command and landing evidence

Reconstructing original selection state preserved all1173 original command
selection snapshots. It found no qualifying missing SCV manager repeat, and an
additional original direct-command check found no unmatched direct TrainSCV label.
The399 unknown manager contexts remain unknown; this does not justify inventing
commands across selection changes.

Four issued requests were mistakenly omitted because before/after queue counts
were unchanged. Two SCV requests span a completion: the old worker finishes while
the new order joins the queue. The other SCV request and one Hellion request are
censored by the record's four-order limit. Plan06 retains all243 prior instructions
and restores these four, totaling247. It claims issued requests, not exact paid
starts or successful fifth-queue admission.

Native21 resolves179/247 and stops on a Factory landing correction. The human
changed the destination nine loops after the first command. The executor now
retires an older unsubmitted landing when its unqueued correction is already due,
and permits a flying building to retarget while its orders are Move/Land.
Native22 independently verifies the Factory actually lands at(148.5,40.5), first
at9744, and resolves186/247. It then stops on a Cyclone request with85 minerals.
Its21 supply warnings all retain matching zero-progress training orders, with no
other action errors. CPU peaks5.3%; native21 peaks6.1%.

Restoring the requests and repairing landing improves command execution coverage.
It **does not improve the same-cutoff worker birth count**: all three native runs
still have45 births before9224. Comparing54 workers at a later stop against45 at
an earlier stop would falsely suggest an economic improvement.

## Next experiment

Use the existing scripted Hard baseline's reactive supply behavior as the reference
for an explicitly declared supply-assistance ablation through the human execution
layer. Base supply decisions on current units, pending construction and paid queues,
not future source replay outcomes. Preserve the original fixed-timing result.
Measure worker births, queue stalls, actual completed Depots, resource spending and
instruction coverage at the same cutoffs. Inspect failures before fitting again.

If that ablation helps, give imitation a state-dependent supply decision and retain
broad raw controls. Declare exactly which decisions are learned versus executed
by primitives. Do not silently add a strategic build-order recipe or count improved
scripted execution as learned competence.

## Reproducible evidence

- `logs/roadmap/native-worker-economy-20/audit.json`: tracker births/deaths and income.
- `logs/roadmap/worker-manager-selection-01/audit.json`: selection reconstruction.
- `logs/roadmap/fixed-human-production-plan-06/verification.json`: independent queue counterexamples, retained instructions, source hashes, replay seeds and actual corrected landing.
- `logs/roadmap/worker-queue-stalls-22/audit.json`: complete stall intervals, sampled source/native queues and bound inputs.
- `logs/roadmap/verify_plan06_native21_22.py` and `audit_worker_queue_stalls_22.py`: executable verifiers, with archived copies beside their receipts.

Landing regressions and the full suite pass549 tests with32 optional skips. The
full human imitation, micro learning, learned Hard and higher-difficulty roadmap
remains incomplete.

October7 follow-up: the [reactive-supply experiment](reactive-supply-assistance-result.md)
is now verified. Native25 produces53 SCVs versus45 by9224 and reduces confirmed
stalls159.29→10 combined producer-seconds. It preserves187/247 instructions and
stops at the same later Cyclone funding deadline10552. This closes most of the
observed worker gap through an explicit scripted assist; no learned win is claimed.
