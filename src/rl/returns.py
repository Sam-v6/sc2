"""Carry delayed outcomes back over macro decisions without crossing game boundaries."""


def remember_episode(policy, transitions, steps=32):
    for index, (state, action, _, _, _, _) in enumerate(transitions):
        total, discount = 0., 1.
        for _, _, reward, nxt, mask, terminal in transitions[index:index + steps]:
            total += discount * reward
            discount *= policy.gamma
            if terminal:
                break
        policy.remember(state, action, total, nxt, mask, terminal, discount=discount)
