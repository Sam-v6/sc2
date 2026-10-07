# Demonstration quality and recovery coverage

An outcome audit of the existing14raw professional replays independently compares
original game metadata with decoded replay details, preserving teacher player
identity and source hashes. Detail race names are localized; public SelectedRace
is used for canonical race and Result is cross-checked against details.m_result.
The audit uses no downloads, fitting or native outcome labels.

| Teaching opponent | Winning examples | Losing examples |
| --- | --- | --- |
| Terran | 1 | 1 |
| Zerg | 3 | 1 |
| Protoss | 4 | 1 |

All three development examples are wins (oneTvZ,twoTvP); there is noTvTdevelopment.
Winners include Clem(294TvT,870TvZ,1038TvP), uThermal(163TvZ), SpeCial(1032TvZ),
HeRoMaRinE(955TvP) and TIME(991/1085TvP). Losing teaching examples are839(uThermal),
523(BackupI) and130(Clem). This names source handles, not an unsupported current
player ranking or an inference about every player's identity.

The failed retrieval run repeatedly selects losing game523 after90seconds.
Its observed workers are18around150seconds,25around300,37around450 and56around600.
Winning TvZ sources870/163/1032 have37/38/40workers around300seconds; the two with
late coverage have73/71around600. Thus the selected low-worker example is a
corpus/selection concern grounded in source outcome and economic trajectory.
This does not establish that loss caused every bad target: losing expert games
can contain useful decisions and recovery, and winning games can contain mistakes.

The next imitation experiment should explicitly distinguish successful economic
trajectories from losing recovery states, retain all original data, and avoid
claiming economic similarity is complete strategic equivalence. Winning-only
selection would leave oneTvTteaching game, making nearest-other-game support
unestimable for that cohort. Additional independent winning TvT examples are
needed before claiming all-race support. No new library/controller is promoted.

Artifacts: `logs/roadmap/human-demonstration-outcomes-01/{audit,verification}.json`;
source identities, outcomes, economic-stage samples and hashes are recorded.
