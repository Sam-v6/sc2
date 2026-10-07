"""Unique learned production intentions through delays, retries and expiry."""


def remaining_budget(budget, cost):
    return tuple(max(0, value-price) for value, price in zip(budget, cost, strict=True))


class ProductionIntents:
    def __init__(self):
        self.intents, self.pending, self.expired = {}, {}, {}
        self.sequence = 0
        self.events = []

    def plan(self, goals, queued, loop):
        for goal, count in goals.items():
            if count <= queued.get(goal, 0) or any(i['goal'] == goal for i in self.intents.values()):
                continue
            if goal in self.expired:
                if loop <= self.expired[goal]:
                    continue
                del self.expired[goal]
            self.sequence += 1
            item = dict(goal=goal, admitted=loop, expires=loop+1008, origin_count=count)
            self.intents[self.sequence] = item
            self.events.append(dict(event='admitted', ticket=self.sequence, **item))

    def requests(self):
        return [i['goal'] for ticket, i in self.intents.items() if ticket not in self.pending]

    def remaining(self, goal):
        return int(goal in self.requests())

    def reserve(self, goal, actor, loop):
        if not self.remaining(goal) or any(p['actor'] == actor for p in self.pending.values()):
            raise ValueError('No unassigned intent or actor already assigned')
        ticket = next(t for t, i in self.intents.items() if i['goal'] == goal)
        self.pending[ticket] = dict(goal=goal, actor=actor, loop=loop, acknowledged=False)
        self.events.append(dict(event='submitted', ticket=ticket, **self.pending[ticket]))
        return ticket

    def acknowledge(self, ticket, success):
        self.events.append(dict(event='acknowledged' if success else 'rejected', ticket=ticket))
        if success:
            self.pending[ticket]['acknowledged'] = True
        else:
            del self.pending[ticket]

    def reconcile(self, active_orders, owned_tags, loop):
        changes = {}
        for ticket, item in list(self.intents.items()):
            pending = self.pending.get(ticket)
            if pending and pending['acknowledged'] and (pending['actor'], item['goal']) in active_orders:
                status = 'observed_order'
                del self.intents[ticket]
            elif loop >= item['expires']:
                status = 'expired'
                self.expired[item['goal']] = loop
                del self.intents[ticket]
            elif pending and pending['actor'] not in owned_tags:
                status = 'actor_lost'
            elif pending and pending['acknowledged'] and loop-pending['loop'] >= 128:
                status = 'unobserved_timeout'
            else:
                continue
            self.pending.pop(ticket, None)
            changes[ticket] = status
            self.events.append(dict(event=status, ticket=ticket, loop=loop, goal=item['goal']))
        return changes
