"""Fit a strategy head to 3.16.1 ladder replay labels (winning Terran player-games only).

Usage: strategy_human_fit_01.py EXTRACT_DIR OUT_DIR
Holds out replays whose hash starts with 0 or 1 (~1/8). Reports held-out per-head accuracy
and within-one accuracy for count heads; no gate, since human targets are noisier than rules.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

from src.learning.strategy_policy import HEADS, StrategyPolicy

EPOCHS, HIDDEN, BATCH = 40, 128, 4096


def load(rows):
    xs, ys = [], {h: [] for h in HEADS}
    for row in rows:
        data = np.load(row['out'])
        xs.append(data['x'])
        for h in HEADS:
            ys[h].append(data[h].astype(np.int64))
    return torch.tensor(np.concatenate(xs), dtype=torch.float32), {h: torch.tensor(np.concatenate(v)) for h, v in ys.items()}


def main():
    extract, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=False)
    torch.manual_seed(0)
    torch.set_num_threads(4)
    rows = [json.loads(line) for line in (extract/'receipts.jsonl').open()]
    rows = [r for r in rows if r['status'] == 'completed' and r['result'] == 1]  # 1 = Victory
    test_rows = [r for r in rows if r['replay'][0] in '01']
    train, test = load([r for r in rows if r['replay'][0] not in '01']), load(test_rows)
    init = StrategyPolicy.initialize(train[0].shape[1], HIDDEN, np.random.default_rng(0)).params
    params = {k: torch.tensor(v, dtype=torch.float32, requires_grad=True) for k, v in init.items()}
    optimizer = torch.optim.Adam(params.values(), lr=1e-3)

    def logits(x):
        h = torch.tanh(x @ params['w1'] + params['b1'])
        return {head: h @ params[f'{head}_w'] + params[f'{head}_b'] for head in HEADS}

    n = train[0].shape[0]
    for epoch in range(EPOCHS):
        for idx in torch.randperm(n).split(BATCH):
            optimizer.zero_grad()
            o = logits(train[0][idx])
            loss = sum(torch.nn.functional.cross_entropy(o[h], train[1][h][idx]) for h in HEADS)
            loss.backward()
            optimizer.step()
    with torch.no_grad():
        def accuracy(data):
            o = logits(data[0])
            exact = {h: float((o[h].argmax(1) == data[1][h]).float().mean()) for h in HEADS}
            near = {h: float(((o[h].argmax(1) - data[1][h]).abs() <= 1).float().mean()) for h in HEADS if h != 'attack'}
            return dict(exact=exact, within_one=near, frames=int(data[0].shape[0]))
        report = dict(train=accuracy(train), held_out=accuracy(test), final_batch_loss=float(loss),
                      games=len(rows), held_out_games=len(test_rows), hidden=HIDDEN, epochs=EPOCHS)
    policy = StrategyPolicy({k: v.detach().numpy() for k, v in params.items()})
    policy.save(out/'policy.npz')
    report['policy_sha256'] = hashlib.sha256((out/'policy.npz').read_bytes()).hexdigest()
    report['bindings'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                          (Path(__file__), Path('src/learning/strategy_policy.py'), extract/'receipts.jsonl')}
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['held_out'], indent=1))


if __name__ == '__main__':
    main()
