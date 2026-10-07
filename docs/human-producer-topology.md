# Winning human plan: preserve producer and addon identities

The first 600 seconds of Clem's winning game 870 contain five observed addons
used by multiple production buildings. A plan that treats each building's addons
as independent inventory misses these transfers. Native playback must preserve
the identities of both buildings and addons across lift, movement and landing.

The source audit reconstructs unique addon proximity at the standard offset
(2.5, -0.5) from each grounded producer. It records 58 producer state transitions
and 80 accepted producer commands, with no ambiguous geometric matches. A
separate verifier reconstructs all 138 rows from the original converted binary,
checks the input hashes, and confirms five shared addon identities. This proves
observed geometry, not native attachment flags or command acceptance.

| Source addon tag | Observed producer sequence |
| --- | --- |
| 4362600450 | Barracks 4355784706 → Factory 4360503299 |
| 4369154049 | Barracks 4355784706 → Starport 4363386885 → Factory 4368891916 |
| 4377018370 | Barracks 4355784706 → Factory 4392484873 |
| 4353949700 | Barracks 4355784706 → Factory 4397203458 |
| 4403232769 | Barracks 4355784706 → Factory 4398252033 |

The initial Barracks starts its Reactor at loop 2837. The Reactor is first seen
at 2857; the Barracks has lifted by 3700 and the Factory occupies its old addon
site at 3723. The same Barracks builds a TechLab at 4000, seen at 4003, then lifts;
the Starport occupies that site at 4724. Later a Factory occupies this same TechLab
site at 8507. These observations supplement the separately reconciled issued
Lift/Land/addon commands; they do not replace those commands with future outcomes.

During landing, the converted unit can briefly retain a Flying type while its
`is_flying` flag is false. Addon types can briefly be generic TechLab/Reactor
before changing to the receiving building's addon type. Source compilation must
retain full tags and use the observed flying flag for geometric matching. The
serialized `add_on_tag` is truncated to eight bits and cannot identify attachments.

For the fixed-plan native test, bind each source producer to a native producer
once, retain the binding through lifts, and bind each addon to its observed native
foundation. Preserve landing-site relationships instead of issuing each landing
near an arbitrary base. Verify actual native addon tags and queried production
abilities before the subsequent unit/research ticket. If a required transfer
fails or its actor is lost, report the first divergence; do not silently replace
the plan with a scripted addon quota. This is an execution diagnostic before
another imitation fit, not a learned-policy result.

Audit, verifier, archived scripts and input hashes are in
`logs/roadmap/human-producer-topology-01`. Both scripts terminated successfully.
No simulation, model fitting or RL ran for this audit.
