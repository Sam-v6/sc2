# Concentrated collection from the strongest learned policy

The strongest retained kills-only Easy40 policy scores 12/30 with greedy
choices. Standard frozen sampling previously lost all six small-probe cases,
and further Easy/Medium/Hard training regressed. The infantry-capability
continuation also regressed to 0/30. Small measured update KL alone does not
explain the macro regression.

In the parent's first four sampled Hard training games (3,070 decisions), only
50.4% of decisions with multiple legal actions matched its greedy choice. The
mean greedy probability in those states was 50.2%; 26% of all decisions were
forced single-legal states. This is conditional trajectory evidence, not proof
of sampling causing losses. Receipt: `logs/audit/kills-parent-sampling-profile.json`.

## Bounded checks

1. Preserve the parent's weights, Adam moments, RNG, counters, cadence, reward,
   observations, action space and micro. In an isolated archive, introduce only
   categorical temperature 0.5, with strict checkpoint settings and consistent
   NumPy and Torch probabilities/likelihood gradients. Positive temperature
   preserves greedy choices initially; sampled behavior deliberately changes.
2. Verify distribution odds, masks, likelihood bias gradients, strict context,
   full suite and Torch integration. Record metadata-only migration and array
   equality. Do not mix rollouts between contexts.
3. Run frozen sampled Hard30 for temperature 1 and 0.5 from the same untouched
   parent, seed 20000, all races, five fixed builds, both maps, 1200 game seconds,
   300 wall seconds and four workers each. Verify terminal receipts, matching
   opponent and policy seeds, and immutable bytes. This is development only.
4. Sharper collection warrants one bounded Hard40 continuation only if it yields
   at least four wins and at least two more wins than the matched temperature-1
   sample. This is an experiment-allocation heuristic, not statistical proof or
   acceptance. If it qualifies, verify isolated training/resume first, then
   train from the untouched migrated initial, retain batch checkpoints and
   evaluate its final frozen greedy and sampled policy separately.
5. Retain the best existing model. Acceptance still requires the documented
   reliable Hard target and untouched final seed bank; no macro recipe is added.

## Verified implementation

The temperature tests failed before implementation; the corrected isolated source
passes 83 tests, including actual Torch update/resume integration. Temperature
is applied to logits in both implementations. Source archive:
`logs/audit/ppo-concentrated-source`.

The migration changes only `settings.temperature=0.5`. Every other metadata
field and every numeric checkpoint array is exact. On 406 retained winning-game
observations, initial argmax choices match; mean maximum probability increases
from 0.551 to 0.615. This is not gameplay improvement evidence. Receipt:
`logs/ppo-concentrated/migration.json`. Immutable initial SHA-256:
964a3547db2bb2282475157124bc56b07d15a860a090315366761501b368ec34.

Both frozen sampled Hard30 comparisons are running. Main production code and
all retained prior sources/models remain unchanged.
