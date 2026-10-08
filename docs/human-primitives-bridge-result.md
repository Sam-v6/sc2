# Human production with verified execution primitives

October6,2026. RL remains paused. This intermediate experiment learns52production
families from professional replays; it does not replace the broader raw-command
roadmap. Gas quotas, physical placement, attack timing/destinations and combat
micro are explicitly scripted assistance. No worker or army production fallback
is allowed. Scripted baseline30/30 remains separate evidence.

## Execution changes

The production bot now uses shared fog-safe mining, interrupted construction
resumption, MULEs, depot lowering, healing, stim and per-unit combat. Combat runs
between forecasts atstep8; selected and pending production actors are protected.
Ground army grouping includes Marauders and other ground-capable military types.
An unaffordable request no longer blocks cheaper learned requests. Tests cover
ownership, resource deferral, between-forecast combat and no invented production.

## Supervised fit and independent verification

`logs/roadmap/human-production-goals-02` uses the independently repaired corpus:
5,378teaching and976previously used development windows. Reserved games remain
untouched. Targets are original own production outcomes in the next1008loops;
future events never become inputs.128ExtraTrees, leaf4, two threads, same bounded
budget as the earlier count experiment. Fit17.42seconds. Reloaded predictions,
metrics and6,354outcome labels independently reconstruct. All976development
feature vectors exactly match the live feature path.

Development building precision/recall55.2/57.4percent and military76.4/78.6percent.
All-family macroF1.2995 beats teaching-mean.0695; countMAE.1600 beats zero.2526 and
teaching-mean.2759. These measures are offline evidence, not game competence.

## Native canary: engineering verified, macro failed

`logs/roadmap/human-goal-native-03/canary`: AcropolisLE, Zerg, VeryEasy/Macro,
seed816003,240game seconds. Native supervision returned the expected horizon
cutoff/Tie in16.983wall seconds, peak6.2percent whole-host CPU. No callback error;
138submitted commands succeeded. The saved trace independently verifies112
forecast frames and560micro frames, model predictions, unique command actors,
pending actor protection, production acknowledgement counts and observed births.
This is not a win and proves no combat strength: there was no army to exercise.

Actual observed production:15new SCVs,1Refinery,2Command Centers and8Supply Depots.
No Barracks appeared despite20forecasts requesting one. Initial Depot forecasts
lasted loops0–240; atloop240 resources were85minerals and a Refinery consumed75.
Depot forecasts next appeared atloop3408, when the first Depot command was issued
(about152game seconds). Barracks forecasts ended atloop912, before a Depot existed.
Atcutoff27workers,3bases andzeroarmy existed. The primitive layer therefore
successfully executed some requests, but the count-only policy and forecast
replacement did not preserve a usable opening sequence.

The trace establishes this ordering failure, not that one timing model will fix
it. Keep counts/checkpoint/canary frozen. The next bounded experiment must learn
ordering or urgency from human outcomes/commands and specify how unfulfilled
requests persist without duplicate starts or endlessly reset deadlines. Do not
repeat the unchanged six-game panel, script macro priorities and call them learned,
or unlock RL on offline accuracy. Broader action imitation and learned micro
still remain required.
