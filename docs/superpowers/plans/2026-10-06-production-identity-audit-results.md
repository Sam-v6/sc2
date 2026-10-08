# Human production identity recovery result

The frozen six-game identity audit is closed. The separate professional corpus
`logs/roadmap/pro-demonstrations-production-08/` contains 3,546 command examples,
146 more than the prior six-game corpus. No checkpoint changed, optimizer ran,
native game launched or RL occurred. Reserved replay evaluations remain untouched.

| Recovered human command | Count |
| --- | ---: |
| Train Hellion | 74 |
| Train Siege Tank | 35 |
| Train Widow Mine | 15 |
| Train Thor | 1 |
| Morph Orbital Command | 18 |
| Morph Planetary Fortress | 3 |

The replay-reader producer's exact unit name identifies a unique engine unit and
its unique production ability, with matching command index. This corrects ordinary
name differences such as BuildSiegeTank versus Train SiegeTank. Numeric unit IDs
from the fallback reader datapack are never joined to raw engine IDs. The complete
command still requires original selection, supported flags, target, loop and mutual
uniqueness against converted actions. No manual substitution table or guessed actor
was introduced. Ineligible and ambiguous events remain unresolved.

All 3,400 baseline command serializations reproduce unchanged. There are no
contradictions between proposed metadata identities and retained commands. An
independent correspondence graph reconstructs all 3,546 accepted identities, actor
groups, precise targets and queue flags without using the reconciliation helper.
Independent review found no blockers; its suggestion to compare every retained
serialization was applied and the audit rerun before importing.

The original importer rebuilt all six sources sequentially into a new directory,
retaining the original issue-loop phase proof, source player/user identity, fog
filter and missing-field declarations. All six imports terminated successfully.
Peak whole-host CPU was 8.3%, below the 80% guard; no GPU or download was involved.
No prior corpus was edited.

Every reconstructed causal history and next-action delay matches the complete
ordered human event stream, including still-unknown events. All 3,400 prior
observations and command labels remain identical apart from their now-more-complete
history and timing supervision. Source validation and engine vocabulary checks pass
(1,970 unit types, 3,801 abilities, 296 upgrades). 3,544 commands are representable;
the same two previously excluded human unit targets remain outside observed
candidates. All 146 newly recovered commands are representable.

Evidence under `logs/roadmap/production-identity-audit-01/`:

| Artifact | SHA256 |
| --- | --- |
| audit.json | 11ffdf228a863bb79740102f45609174b5cf8aec424f80ed45d001b8c3b0d51a |
| match-verification.json | d2235d31b9550020be95394ec7a9c384c9db64c22fcdfa37b2dec6abb20e2f74 |
| corpus-verification.json | d55447ab6aa8c9e09ce8fc88120fff331f67b925872252ac923c6ffaf860df37 |
| encoding-verification.json | fc8926d05c50cb62034721870a134c2493f5780c8af3ab4e3136378451af8dff |
| import-results.json | b2bd23c9ddf6d72509bd3013f26cdb9f1522a3574205ec90b21c57382cbb4860 |

The encoding-verification receipt additionally records all six eligibility and
representability checks. These are still six correlated, partial professional
trajectories, with 1,130 unresolved issued events. They are not complete native
professional replay reconstruction or additional independent games. Data recovery
does not establish imitation accuracy, generalization, army production in native
games, micro transfer, Hard wins or higher-difficulty competence.

Validation: normal suite passes (397 tests, 31 optional skips), focused producer
identity tests pass, Ruff/diff checks pass and independent read-only review passes.

Next choose a bounded human-only imitation experiment using the repaired corpus.
Measure the recovered production families explicitly alongside full command fidelity
and development game generalization; do not promote a policy on label recovery alone
or resume a previously failed fit unchanged. RL remains deferred until useful
human imitation/native competence is established.
