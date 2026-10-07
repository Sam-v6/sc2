# Winning human production: queue and missing-addon audit

A fixed winning game is a useful execution diagnostic only if its important
production instructions survive import. The audit of game870 (Clem, Terran
versus Zerg, verified human win) finds a concrete omission before native playback.
No fitting or RL ran.

The existing converted record contains1,900 pre-effect observations, from loop12
to19382. Median gap is7loops,95th-percentile29, maximum259. Among224 matched
production command/actor pairs,220 have an increased count of that production
order in the next observation. Four already had that order and show no increase
(three SCV and one Hellion commands). They must not become four automatic extra
production tickets. No matched or unresolved command to the same recovered actor
occurs in these before/after intervals. This is observed queue evidence, not an
exact resource-payment or completed-unit attribution claim.

There are **zero matched addon-building commands** in the imported game. The
original replay tracker independently contains **nine own addon starts**:
five Barracks TechLabs/Reactors, one Starport Reactor and three Factory addons.
Thus a plan assembled only from imported command labels would omit required
production setup. The original source really produced addons; this gap is not
explained by the human forgetting them.

The conversion and reconciliation use different ability representations. At loop
3516 the original command is a Factory-specific lift while the converted action
uses generic Lift3679. At3700 the same applies to Land3678. Existing direct name
matching rejects these aliases. At2837/4000/5164, raw Barracks addon commands have
a point target while converted BuildReactor3683/BuildTechLab3682 have no target;
the first three also contain unsupported flag0x1000000. Their native descriptors
mark instant placement. These differences need source-backed reconciliation,
not unrestricted acceptance of unknown flags or discarded targets. Legacy names
for other unresolved actions are not assumed correct without native conformance.

The original870 replay needs engine76052; installed Linux engine75689 cannot
reconstruct it. Existing converted observations, raw selections/actions and
tracker chronology suffice to investigate these specific omissions without a
new engine download. Reliable addon attachment IDs are absent from the converted
format, and queues are truncated after four orders. Those limitations remain
explicit. Construction starts can help check geometry but cannot by themselves
prove which command attached an addon to a producer.

Next repair and test generic Lift/Land reconciliation with verified actor type,
selection, original targets and mutually unique identities. Then investigate
addon target/flag semantics and producer swaps using the existing full record.
Reimport into a new corpus and compare all old accepted labels before any new
training or fixed-human-plan execution. Do not silently reuse the current corpus
as a complete production plan, substitute a scripted addon quota, or label this
source audit as learned strength.

Independent verification reconstructs all224 queues from the original binary
record and decodes addon starts from the original replay. Bound sources,
audit and verification receipts are preserved in
`logs/roadmap/human-queue-transitions-01`. Both scripts finished successfully.
