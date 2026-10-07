"""Stage A: imitate scripted_targets/scripted_attack from the Hard baseline traces.

Holds out two games per race. Gate: every head >= 95% held-out frame accuracy.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from src.learning.strategy_imitation import trace_examples
from src.learning.strategy_policy import HEADS, StrategyPolicy

PANEL = Path('logs/roadmap/primitives-hard-baseline-01/panel')
OUT = Path('logs/roadmap/strategy-imitation-fit-01')
HELD_OUT = {'Terran-Macro-AcropolisLE', 'Terran-Air-AbyssalReefLE', 'Zerg-Rush-AcropolisLE',
            'Zerg-Power-AbyssalReefLE', 'Protoss-Timing-AcropolisLE', 'Protoss-Macro-AbyssalReefLE'}


def load(games):
    xs, ys = [], {h: [] for h in HEADS}
    for game in games:
        types = {u['unit_id']: u for u in json.loads((game/'game.primitives.data.json').read_text())['units']}
        x, y = trace_examples(game/'game.primitives.jsonl.gz', game.name.split('-')[0], types)
        xs.append(x)
        for h in HEADS:
            ys[h].append(y[h])
    return torch.tensor(np.concatenate(xs)), {h: torch.tensor(np.concatenate(v)) for h, v in ys.items()}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    torch.manual_seed(0)
    torch.set_num_threads(4)
    games = sorted(p for p in PANEL.iterdir() if (p/'game.primitives.jsonl.gz').is_file())
    assert len(games) == 30 and HELD_OUT <= {g.name for g in games}
    train = load([g for g in games if g.name not in HELD_OUT])
    test = load([g for g in games if g.name in HELD_OUT])
    inputs, hidden = train[0].shape[1], 128
    init = StrategyPolicy.initialize(inputs, hidden, np.random.default_rng(0)).params
    params = {k: torch.tensor(v, requires_grad=True) for k, v in init.items()}
    optimizer = torch.optim.Adam(params.values(), lr=3e-3)

    def logits(x):
        h = torch.tanh(x @ params['w1'] + params['b1'])
        return {head: h @ params[f'{head}_w'] + params[f'{head}_b'] for head in HEADS}

    for epoch in range(6000):
        optimizer.zero_grad()
        out = logits(train[0])
        loss = sum(torch.nn.functional.cross_entropy(out[h], train[1][h]) for h in HEADS)
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        def accuracy(data):
            out = logits(data[0])
            per = {h: float((out[h].argmax(1) == data[1][h]).float().mean()) for h in HEADS}
            exact = torch.stack([out[h].argmax(1) == data[1][h] for h in HEADS]).all(0)
            return dict(per_head=per, all_heads=float(exact.float().mean()), frames=int(data[0].shape[0]))
        report = dict(train=accuracy(train), held_out=accuracy(test), final_loss=float(loss),
                      held_out_games=sorted(HELD_OUT), hidden=hidden, epochs=6000)
    report['gate'] = dict(threshold=.95, passed=all(v >= .95 for v in report['held_out']['per_head'].values()))
    policy = StrategyPolicy({k: v.detach().numpy() for k, v in params.items()})
    policy.save(OUT/'policy.npz')
    report['policy_sha256'] = hashlib.sha256((OUT/'policy.npz').read_bytes()).hexdigest()
    report['bindings'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                          (Path(__file__), Path('src/learning/strategy_policy.py'), Path('src/learning/strategy_imitation.py'))}
    (OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(held_out=report['held_out'], gate=report['gate']), indent=1))


if __name__ == '__main__':
    main()
