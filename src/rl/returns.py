"""Carry delayed outcomes back over macro decisions without crossing game boundaries."""


def remember_episode(policy, transitions, steps=32):
    for index, (state, action, _, _, _, _) in enumerate(transitions):
        total, discount = 0., 1.
        for offset, (current, chosen, reward, following, legal, ended) in enumerate(transitions[index:index + steps]):
            # The worker policy stays frozen during collection. Do not credit
            # earlier actions for later nongreedy exploration.
            if offset and chosen != policy.act(current, mask, explore=False):
                break
            nxt, mask, terminal = following, legal, ended
            total += discount * reward
            discount *= policy.gamma
            if terminal:
                break
        policy.remember(state, action, total, nxt, mask, terminal, discount=discount)
