# Panel offsets (fixed before the evaluation panel ran)

zero-terran.json = strategy-cem-01 mean after iteration 7 for Zerg and Protoss; zero offsets for Terran.

- cem-01 TvT degraded 11 -> 6/20 (noisy elites from random build draws); not used.
- cem-02 (TvT, common random numbers) wins/50 by iteration: 15, 20, 31, 24, 25; the
  unperturbed control never clearly beat its candidates or the zero start, so no TvT
  offsets are adopted. Choosing between options on the panel seeds would leak the test.
- Evaluation: scripted-defense-veryhard-panel-01 got 23/30 on seeds 850001+; this panel uses
  fresh seeds 860001+. Pass = more than 23 wins.
