# Combat order diagnostic: complete

The four observation-only games126000–126003 completed without failures or
training updates (native session7514, exit0). Independent review verifies all
four cases/2,384decisions, frozen source/context, ordinary actions/rewards,
typed scripted non-PPO data, journals, replay headers and trace provenance.
CPU31two-second whole-machine windows average15.4787%, maximum22.7886%.

Actual medivac engine orders include MEDIVACHEAL_HEAL:267entries in Rush and391
in Timing. These include179/295entries with wounded Marine/Marauder within4,
and226/355within6. Energy-drop intervals84/68 and nearby positive HP deltas86/67
corroborate that healing occurs. **Repeated movement commands do not establish
missing healing.** Order lists can contain HEAL and MOVE together; entry counts
are not mutually exclusive medivac frame frequencies, and omitted order targets
prevent definite recipient attribution.

Tank air-only observations excluding visible ground structures total257
unit-frames at range12 and235at range14. Corresponding SIEGEMODE order entries
are86/78. This demonstrates the existing all-enemy siege guard reacts to air
targets, not whether correcting it improves wins.

All four incidental outcomes are Victory. This bank has no strength gate and
cannot revise the closed teacher's failed all-race competence result. No cloning,
promotion, fitting, deployment change or replay viewing follows from these wins.

Evidence: `logs/macro-teacher/micro-order-diagnostic/`,
`logs/audit/micro-order-diagnostic-complete-independent-review.json`,
`logs/audit/micro-order-evidence-source/descriptive-summary.json`, and the
separate order-count clarification in that audit source directory.

Next: retain existing medivac behavior; verify a ground-aware tank guard in a
controlled physical fixture before a separately frozen matched game comparison.
Composition and regrouping remain possible causes of the original losses.
