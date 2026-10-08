# Missing human production identity audit

Follow-up to the closed production forecast coverage audit. Current work is human
imitation, with no fitting, RL, native games or reserved replay evaluation here.

Use the same six fitted professional replay sources and their original source
bindings. Do not modify the existing corpus. Quantify potential recovery first.

The current reconciliation demands an exact replay ability name/native friendly
name match. Ordinary production has spelling differences (BuildSiegeTank versus
Train SiegeTank). Existing sc2reader uses a fallback 70154 datapack for these 76052
replays; its unit IDs are not raw engine IDs. No direct numeric ID joins or freeform
name substitutions are allowed.

Inspect producer metadata instead: sc2reader's named build unit must match exactly
one engine unit name, whose production ability must exist and have the same command
index. This establishes a candidate only. Quantify unresolved candidate counts by
ability and failure reason. Explicitly retain cases with no unique name match,
missing producer metadata, conflicting indexes or conflicting metadata.

To test command identity, require original selection, flags, loop, target and
mutually unique converted-action correspondence as before. Audit retained commands
under the proposed metadata test for contradictions and independently inspect
examples of each newly recoverable production family. Record source/version hashes,
candidate mappings and every rejection. Do not weaken chronology or fog checks.

If metadata and converted-action evidence disagree, stop that mapping. If identities
are corroborated, write a separate new corpus with original observations and a new
receipt, leaving old corpus/checkpoint evidence intact. Revalidate causal history,
delay labels and source bindings. Neither an identity count nor reconstruction of
human labels proves policy competence; choose a separate imitation fit afterward.
