# Idempotent combat-stance experiment

Frozen Hard traces switch attack/retreat at a median interval of 1.07 seconds.
The current mask excludes the active stance, though wait can retain it. Replaying
exact logged states with both stance choices allowed makes the frozen actor retain
its current stance on 222/384, 254/411 and 175/307 switch selections in the studied
Zerg win/Terran loss/Protoss loss. This is counterfactual selection evidence, not
proof of a bug or of stronger game performance. Production banks also grow while
most tech units are never chosen; avoid attributing all losses to stance alone.

1. Archive the finite source independently; do not alter either live continuation.
   Allow both attack and retreat whenever an army exists. Repeated selection of
   the current stance is successful/idempotent: it must not reset elapsed stance
   time or request new combat orders. A real mode change still updates both.
   No scripted attack timing, minimum hold period or forced aggression is added.
2. Add red-to-green tests for both active/inactive army masks, repeated stance
   commands, and pending order-change flags. Run the complete archived suite.
3. Load immutable finite Easy40 bytes without changing parameters, reward, schema,
   RNG or learner settings. First evaluate six matching frozen Hard development
   games. Record switches, stance duration, terminal outcomes and engine failures.
   Never treat issued commands or counterfactual preferences as actual victories.
4. If the frozen probe improves, investigate wider frozen scope and a separately
   retained training continuation before default promotion. Preserve all controls,
   original sources and acceptance seeds. If weak, inspect replay/order lifecycles
   and production opportunities before introducing another intervention.

Verification: the archived source passes 71 tests, including two red-to-green
checks. Frozen Hard6 with the same finite Easy40 bytes lost all six games,
without failures or model mutation. Counterfactual stance retention also replaces
some production choices and does not simulate new dynamics. No strength gain
is established, and the default mask/command behavior remains unchanged.
