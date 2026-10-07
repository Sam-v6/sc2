# Human inventory retrieval: offline diagnostic

The failed inventory regressor remains closed. This experiment does not refit it.
Instead, choose one real professional-human inventory example: what units and
buildings that player had 45 seconds after a recorded observation. Match the
observation by game time, current workers and total town halls. Restrict examples
to the publicly selected opponent race when known; Random uses an unknown cohort.
Do not use hidden assigned race. Do not mix per-unit maxima from different games,
and do not use army/production shortages or resource bank to choose the example.

The existing verified corpus provides 5,378 teaching observations from 11 games
(two TvT, four TvZ, five TvP), with 976 development observations from three games.
Normalization uses teaching-only standard deviations, floored at one. Support
limits use the 95th percentile nearest distance to a different teaching game
within each race cohort. A chosen complete future inventory is held for 1,008
loops; reselection then uses the current economic observation. Source game, row,
current/future loop and inventory-file hash are recorded for every retrieval.

Independent verification reconstructed normalization, cross-game support limits,
all 976 development selections and predictions, and all 281 saved cadence-native
forecasts. Equivalent distance arithmetic exposes symmetric nearest-example ties;
verification checks both the independent minimum distance and the canonical
normalized-arithmetic first-index selection. No model fit, new download, game
simulation or RL update was used for this diagnostic.

| Development game | Supported rows | Mean absolute inventory error | Production-building error |
| --- | --- | --- | --- |
| 887 | 294/294 | 0.2128 | 0.1610 |
| 920 | 517/517 | 0.3490 | 0.1167 |
| 851 | 165/165 | 0.1401 | 0.1434 |

These are retrieval errors, not replacement acceptance metrics for the failed
regressor. Development excludes TvT, and support proximity alone is not a
competence guarantee.

The saved native trace's final 68-worker state retrieves game1032/row488,
current loop11865 and future loop12873: seven Barracks, three Factories and one
Starport, compared with one of each in the native bot. Thus real examples exist
that request materially more capacity in the shown late shortage state.
Across the 141 forecasts after five minutes, 92 request greater total production
capacity; the other 49 request the same capacity. All are within the frozen
support limits. The diagnostic flag requiring greater capacity on *every* late
forecast is false and remains recorded as false. The earlier equal-capacity
choices are a risk for a live controller, not grounds to change the frozen
selection rules.

Next: implement execution of positive target-minus-current inventory deficits,
count foundations immediately and queued births once, retire unissued intents
when satisfied or dropped by a new target, and preserve accepted work. The old
recent-fulfilment rate quota cannot be applied to absolute inventory targets.
Verify these semantics before the already planned matched native comparison;
both arms must use the verified scout. No native competence claim is made here.

Artifacts and receipts: `logs/roadmap/human-goal-retrieval-01/`, with audit and
independent verifier scripts alongside it. The full roadmap remains active;
broad human command imitation, learned micro, RL and learned Hard/higher wins
remain unproven.
