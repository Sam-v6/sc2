"""Account for predicted production and engine work without inventing goals."""

from collections import Counter


class ProductionLedger:
    def __init__(self):
        self.goals = {}
        self.queued = {}
        self.pending = {}
        self.sequence = 0

    def plan(self, goals, queued):
        """Replace predictions; retain acknowledged work not yet observed."""
        self.goals = dict(goals)
        self.queued = dict(queued)

    def remaining(self, goal):
        pending = Counter(item['goal'] for item in self.pending.values())
        return max(0, self.goals.get(goal, 0) - self.queued.get(goal, 0)
                   - pending[goal])

    def reserve(self, goal, actor, loop):
        if self.remaining(goal) < 1:
            raise ValueError('No predicted work remains for this goal')
        if any(item['actor'] == actor for item in self.pending.values()):
            raise ValueError('Actor already has pending work')
        self.sequence += 1
        self.pending[self.sequence] = dict(goal=goal, actor=actor, loop=loop,
                                           acknowledged=False)
        return self.sequence

    def acknowledge(self, ticket, success):
        if success:
            self.pending[ticket]['acknowledged'] = True
        else:
            del self.pending[ticket]

    def reconcile(self, active_orders, owned_tags, loop):
        """Transfer observed work to queue accounting; report lost/unechoed work.

        An accepted command is not a completed unit. Current engine orders replace
        pending accounting once visible. Expiry means no observed order within
        128 loops, not a claimed cancellation or successful production.
        """
        changes = {}
        for ticket, item in list(self.pending.items()):
            if item['actor'] not in owned_tags:
                status = 'actor_lost'
            elif item['acknowledged'] and (item['actor'], item['goal']) in active_orders:
                status = 'observed_order'
            elif item['acknowledged'] and loop - item['loop'] >= 128:
                status = 'unobserved_timeout'
            else:
                continue
            del self.pending[ticket]
            changes[ticket] = status
        return changes
