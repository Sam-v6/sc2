# Primitive and affordance audit

The user asked to focus on primitives, sensory information and the RL approach
when continued training fails to improve. The latest independent-value model
fails its joint frozen-development gate despite better value fits. Do not
extend that arm. Keep final acceptance bank50000 reserved.

A frozen-state action audit covers the retained model's60 games/33,556 states
and the independent-value model's60 games/34,158 states. Both use immutable
checkpoints. Legal masks and accepted command flags do not establish successful
completion of every primitive; verify those separately.

| Action | Retained legal games/states | Independent-value legal games/states |
|---|---:|---:|
| Marauder | 5 /31 | 1 /2 |
| Tank | 43 /135 | 53 /170 |
| Starport | 59 /1,768 | 59 /2,017 |
| Medivac/Viking/Raven/BC | 0 /0 | 0 /0 |

Neither frozen model selects these actions. The new model assigns mean
probability1.31e-5 to Starport when legal,2.57e-4 to Tank and1.60e-5 to
Marauder; the retained untempered distribution assigns0.0791/0.1242/0.1106.
These are actual-state probabilities, not alternative gameplay outcomes.
A late-tech action can be technically implemented yet rarely accessible because
resources, producer queues or prerequisites are absent; diagnose those conditions
rather than assuming the model freely chose among all27 actions.
Receipt: `logs/audit/action-affordance-coverage.json`.

Next, verify actual production primitives in an isolated SC2 debug fixture:
producer/tech readiness, resource cost, legal-mask eligibility, command acceptance,
and completed unit counts for the available Terran unit types. Debug resource/unit
creation belongs only to capability verification, never strength evaluation or
training. Instrument prerequisite/resource/idle-producer reasons and observe
normal frozen trajectories around the rare legal opportunities. Separate a real
executor defect from an action-space/credit-assignment limitation.

Only after those findings choose a learning intervention. Possible directions
include sensing/scouting, persistent macro intent, coherent exploration and
training-scale/credit assignment. Do not add a scripted build order or unit mix.
Consult an Astra ideas agent if useful evidence stalls and concrete next steps
run out, as the user explicitly permitted; that condition has not been invoked.

All subsequent local jobs use `tools/low_load.py`, four or fewer simultaneous
games, eight allowed logical CPUs and lower priority. Numerical libraries use
one thread; learning is CPU-only. Eight CPUs bound this task to25% nominal
logical CPU capacity on this32-thread host, with headroom for the user's below40%
whole-machine preference. Other applications contribute independently. Measure
live load during the next runtime job; the first quiet-profile monitor started
after its four games completed, so it is not evidence of active CPU/GPU use.
Child/grandchild resource inheritance is independently tested. The four quiet
verification games finish without failures or checkpoint changes, and known
seed20013 matches its original winning gameplay trace byte for byte. Those
same-race/build runtime checks are not broad strength acceptance.
