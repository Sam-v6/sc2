# Source-backed human Lift/Land recovery

The command reconciler now recognizes generic converted Lift/Land abilities when
the original replay names a specific producer, such as LiftFactory. It requires
an exact specific catalogue name/index and generic remap, plus matching pre-effect
own producer types for every converted actor. Missing types and wrong producer
families remain excluded. Original selections, precise targets, regular flags and
mutually unique command identities are still checked. Unsupported events continue
to reserve possible action identities; no unknown command flags are accepted.

Two new regression tests reproduced the original rejection and now pass. They
cover matching Factory/FlyingFactory actors, wrong or missing types, precise
landing targets and an unsupported duplicate preventing ambiguous reuse. The
full suite passes 510 tests with 32 optional skips; named-file Ruff and diff checks
pass. This changes source identity reconstruction, not the game policy.

A fresh rebuild of teaching game870 recovers 16 Lift and 16 Land commands. All
804 previously imported command labels remain unchanged, giving 836 labels.
The adapter verifies own actor types against original causal tracker chronology
and same-loop type boundaries before supplying those types to reconciliation.
Independent verification checks raw events, original selections, generic wire
actions, observed actor types, queue flags and precise landing coordinates.
Existing own state, memory, terrain and original labels remain unchanged; 139
current enemy observations on the added rows pass the supplied visibility-grid
check. History can now include the recovered commands. Exact original paid/start
acceptance is not asserted.

Receipts, the new corpus and bound source snapshots are under
`logs/roadmap/human-lift-land-reimport-02`. The first diagnostic used the older
723-label reconciliation and produced755 labels; it is preserved under01 and
was not promoted. The corrected02 run uses the current804-label producer-identity
reconciliation and passes the no-loss gate. Historical corpora and development
games remain unchanged. No training, native gameplay or RL ran.

Addon commands remain omitted. Point-bearing raw addon commands differ from
point-free converted actions; some use unsupported flag0x1000000. Reliable addon
attachment IDs are absent from the converted record. Recovering Lift/Land does
not by itself create a complete production plan. Next verify addon command
identity and target semantics from the original commands, observed actor positions,
tracker construction starts and native catalogue before compiling the fixed
winning-human execution test. Preserve ambiguous cases rather than teach invented
setup or substitute scripted strategic quotas.
