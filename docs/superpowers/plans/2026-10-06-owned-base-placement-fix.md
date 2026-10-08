# Native check of owned-base placement fallback

Live probes02 found engine-approved reachable owned-expansion sites for all
48Barracks/8EngineeringBay/7Depot original rejections. Implement physical fallback
only after the original resolver fails, using complete landed own bases. Keep
original ordering when it succeeds; retain addon pad, spawn-lane, footprint,
native placement and worker path checks. Do not redirect CommandCenter expansion
goals or point-free/addon/upgrade commands. No new strategic demands or caps.

Regression test reproduces original rejection and checks reachable fallback,
complete/landed/own base requirements and preserved expansion intent. After the
full suite/Ruff, freeze native03 with the same human inventory job, assistance,
seed/map/opponent and CPU/600game/240wall limits. No fitting or RL.

Primitive gate: fallback commands retain original goal/ability/actor, use only
owned complete landed base anchors, are native-accepted, have observed native
construction and tracker completion; more completed production capacity than
failed native01's5, at least one completed fallback Depot/Barracks, and no actor
or source-deficit/queue/lifecycle invariant violations. Report unchanged full
mechanism metrics separately; this primitive gate cannot promote human imitation
or replace the original failed comparison gates. Preserve source snapshot.
