# Correct the scout outing deadline

The original transfer canary is closed as failed: selection at 97.5 seconds,
return at 135 seconds, first enemy observation at 248.93 seconds. Its trace shows
a moving SCV at (136.4, 65.8), still short of enemy spawn (142.5, 33.5), when it
turns home. The fixed global deadline allowed only 37.5 seconds because the human
controller completed its Barracks later than the scripted baseline.

Preserve native-01, its failed gate and bound source snapshot. Change only the
outing deadline to selection plus 1,344 loops (60 seconds). Retain selection in
75–135 seconds, one-time scouting, damage retreat at 60% health, actor protection,
no commands to actors present only in memory, and return to own minerals. The
relative deadline never restarts on memory-only observations.

Freeze native-02 with the same AcropolisLE/Zerg/VeryEasy/Rush seed816201,
600 game seconds and 240 wall seconds, count model/prior/profile, CPU-only two
threads and 80% host guard. No learning or RL. Gate: selection in 75–135 seconds,
real visible enemy before 160 seconds, owned acknowledged scout commands,
no production or harvesting overwrite while protected, return/loss no later than
selection plus60seconds plus8loops, and return to mining if surviving. Report
production and result separately; this does not prove learned macro competence.
