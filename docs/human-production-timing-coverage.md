# Human production timing: source coverage is insufficient

The two-second act/wait experiment is closed without a fit. The existing
professional corpus remains useful for command identity, but does not establish
representative quiet-period supervision. Training a timing gate on its retained
examples could reward excessive production requests rather than human timing.

`logs/roadmap/production-decisions-01/` reconstructs 2,044 actual observations
across six teaching and three reused diagnostic games. Observations contain no
human command history or future command arguments. An independent verifier
checks raw identities, positions, health, fog-safe memories, player statistics,
maps, chronological labels and source hashes. Tracker effects occur strictly
before the observation loop; a same-loop MULE death initially exposed an incorrect
boundary in the verifier, which was corrected before verification passed.
The 44-loop selection uses actual observations; it does not interpolate gaps.

The first-event labels retain 468 production and 114 wait teaching examples,
censoring 975. A separate production-specific classification pass in
`logs/roadmap/production-timing-audit-02/` distinguishes gate supervision from
first-command identity. A verified production event proves an act interval even
if an earlier event is unknown. That earlier event still obscures which command
came first. Numeric source ability identities are classified only when supported
by accepted commands from the same game. Regular user production flags are
required for newly classified production intent. Unknown command-manager events
remain possible production; missing converted matches do not establish waiting.
The broad corpus and its unknown history slots are unchanged.

| Role | Actual anchors | Production confirmed | Waiting confirmed | Unknown |
|---|---:|---:|---:|---:|
| Teaching | 1,557 | 816 | 122 | 619 |
| Reused diagnostics | 487 | 194 | 41 | 252 |

Unknown teaching intervals remain 39.8 percent. Among only retained teaching
intervals, 87.0 percent are positive; that is a selected fraction, not a measured
human production rate. Individual games cover only 74.5–79.9 percent of source
elapsed time with these observation windows. The longest anchor gap is 325 loops.
Opening, middle and late counts are recorded per game, including all unknowns.
Neither timing labels nor the missing elapsed time justify treating an absent
command as a negative example. Classification yields 479 teaching windows with
known first production identity; these are not necessarily independent events.

The independent second verifier checks source-event proof references, numeric
ability equivalence, regular production flags, all interval labels, first-command
censoring and exact elapsed-time coverage. Both preparation and classification
jobs are terminal. No model training, simulation or RL ran for this experiment.
Full suite: 560 tests, 32 optional skips. The observation preparation sampled a
4.3 percent host CPU peak; classification did not independently measure a peak.

The next experiment must address missing timing supervision rather than repeat
an act/wait fit on this selected subset. Prefer professional replay extraction
that supplies regular current observations through quiet periods. A bounded
conditional production-identity experiment can still use verified commands,
but any scripted timing must be declared and its wins must not be presented as
learned macro competence. Keep broad actor/target/queue controls and verified
primitive execution; useful native imitation remains required before RL.
