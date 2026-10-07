"""Read-only saved-model stationarity and causal opening-source audit."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.sparse import hstack, vstack
from scipy.special import logsumexp

from src.learning.actor_selection import construction_products
from src.learning.entity_examples import replay_examples
from src.learning.entity_train import DELAYS
from src.learning.intention_probe import probe_features, probe_metrics
from src.learning.teacher_states import teacher_states

ROOT=Path('logs/roadmap/intention-probe-01')
OUT=ROOT/'optimization-audit.json'
assert not OUT.exists()
started=time.monotonic()

def read(p):
    return json.loads(Path(p).read_text())

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

contract,report,verified=(read(ROOT/name) for name in ['contract.json','report.json','verification.json'])
assert verified['report_sha256']==sha(ROOT/'report.json') and verified['contract_sha256']==sha(ROOT/'contract.json')
assert verified['status']=='verified_signal_diagnostic'
config=read('logs/roadmap/joint-professional-fit-05/configuration.json')
paths=[Path(s['dataset']) for s in config['sources'] if s['role']=='teaching']
games={}
source_audit=[]
for path in paths:
    static=read(path/'static.json')['game_data']
    pairs=[]
    labels=[]
    for inputs,label,command,reason in replay_examples(path,*contract['vocabulary'],DELAYS,construction_products(static),spatial=False,missing_fields=True):
        pairs.append(probe_features(inputs,*contract['vocabulary'][:2]))
        labels.append(command.ability)
    games[path.name]=dict(state=vstack([p[0] for p in pairs]).tocsr(),history=vstack([p[1] for p in pairs]).tocsr(),labels=np.array(labels))
    # Fixed audited rows only; inspect available original orders, no inference of legality.
    selected={x['index'] for x in verified['audited_failed_macro_rows'] if x['game']==path.name}
    for index,(row,state) in enumerate(teacher_states(path)):
        if index not in selected:
            continue
        own=[u for u in state['units'] if u['alliance']==1]
        command=row['commands'][0]
        known={u['tag']:u for u in own}
        source_audit.append(dict(game=path.name,index=index,ability=command['ability'],player=state['player'],actor_types=[known.get(t,{}).get('unit_type') for t in command['units']],actor_orders=[known.get(t,{}).get('orders') for t in command['units']],own_type_counts=dict(Counter(u['unit_type'] for u in own)),known_order_counts=dict(Counter(o['ability_id'] for u in own for o in u.get('orders',[]))),history_abilities=[c.get('ability',0) for c in state['recent_commands']],scope='Available causal source values only; no native legality claim.'))
    print(json.dumps(dict(stage='prepared',game=path.name)),flush=True)
result=dict(status='read_only_saved_model_audit',bindings={str(ROOT/n):sha(ROOT/n) for n in ['contract.json','report.json','verification.json']},script_sha256=sha(__file__),folds=[],fixed_source_rows=source_audit,scope='No optimizer updates, feature changes, held/reserved predictions or controller promotion.')
for fold in report['folds']:
    labels=np.concatenate([games[g]['labels'] for g in fold['train']])
    record=dict(train=fold['train'],held=fold['held'],arms={})
    result['folds'].append(record)
    for arm,entry in fold['arms'].items():
        def matrix(g):
            return hstack([games[g]['state'],games[g]['history']]).tocsr() if arm=='both' else games[g][arm]
        x=vstack([matrix(g) for g in fold['train']]).tocsr()
        binding=fold['models'][arm]
        assert sha(binding['path'])==binding['sha256']
        with np.load(binding['path'],allow_pickle=False) as a:
            model={k:a[k] for k in a.files}
        z=x[:,model['columns']].multiply(1/model['scales']).tocsr()
        lookup={int(c):i for i,c in enumerate(model['classes'])}
        targets=np.array([lookup[int(y)] for y in labels])
        logits=z@model['weights']+model['bias']
        lp=logits-logsumexp(logits,axis=1,keepdims=True)
        ce=-lp[np.arange(len(labels)),targets].mean()
        penalty=.005*np.square(model['weights']).sum()
        residual=np.exp(lp)
        residual[np.arange(len(labels)),targets]-=1
        residual/=len(labels)
        gradient=np.vstack([z.T@residual+.01*model['weights'],residual.sum(axis=0)])
        classes,counts=np.unique(labels,return_counts=True)
        baseline_ce=-sum(n*np.log(n/len(labels)) for n in counts)/len(labels)
        dense=z.toarray()
        constant=np.ptp(dense,axis=0)==0
        record['arms'][arm]=dict(train_cross_entropy=float(ce),l2_penalty=float(penalty),objective=float(ce+penalty),frequency_baseline_ce=float(baseline_ce),gradient_max_abs=float(abs(gradient).max()),gradient_l2=float(np.linalg.norm(gradient)),active_columns=len(model['columns']),constant_active_columns=int(constant.sum()),train_metrics=probe_metrics(model,x,labels,report['macro_ids']))
        assert np.isfinite(gradient).all()
        print(json.dumps(dict(stage='audited',held=fold['held'],arm=arm,gradient_max_abs=record['arms'][arm]['gradient_max_abs'],train_macro_recall=record['arms'][arm]['train_metrics']['macro_exact_recall'])),flush=True)
result['seconds']=time.monotonic()-started
assert all(sha(p)==digest for p,digest in contract['bindings'].items())
OUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],seconds=result['seconds'])),flush=True)
