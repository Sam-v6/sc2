"""Read-only independent reconstruction and metric check; never fit a model."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse import hstack, vstack
from scipy.special import logsumexp

from src.learning.actor_selection import construction_products
from src.learning.entity_examples import replay_examples
from src.learning.entity_train import DELAYS
from src.learning.intention_probe import probe_features

OUT = Path('logs/roadmap/intention-probe-01')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def metrics(logits, classes, labels, macro_ids):
    ranked = classes[np.argsort(-logits, axis=1, kind='stable')[:, :3]]
    correct = ranked[:, 0] == labels
    top3 = (ranked == labels[:, None]).any(axis=1)
    lookup = {int(c):i for i,c in enumerate(classes)}
    logp = logits-logsumexp(logits,axis=1,keepdims=True)
    ce = -np.mean([max(logp[i,lookup[int(y)]], np.log(1e-12)) if int(y) in lookup else np.log(1e-12) for i,y in enumerate(labels)])
    gold = np.isin(labels,macro_ids)
    chosen = np.isin(ranked[:,0],macro_ids)
    def rate(n,d):
        return float(n/d) if d else None
    return dict(rows=len(labels),cross_entropy=float(ce),top1=float(correct.mean()),top3=float(top3.mean()),macro_rows=int(gold.sum()),macro_exact_recall=rate((correct & gold).sum(),gold.sum()),macro_family_recall=rate((chosen & gold).sum(),gold.sum()),macro_false_positive_rate=rate((chosen & ~gold).sum(),(~gold).sum()),absent_training_abilities={str(c):int((labels==c).sum()) for c in np.unique(labels) if int(c) not in lookup},per_ability={str(c):dict(rows=int((labels==c).sum()),top1_correct=int((correct & (labels==c)).sum()),top3_correct=int((top3 & (labels==c)).sum())) for c in np.unique(labels)})


contract,report = read(OUT/'contract.json'),read(OUT/'report.json')
assert report['contract_sha256'] == sha(OUT/'contract.json')
assert contract['folds'] == [['294','887','920'],['870','839','851'],['955','991','523']]
assert contract['regularization']==.01 and contract['max_iterations']==100 and contract['wall_seconds']==300
assert contract['spatial'] is False and contract['missing_fields'] is True
if report['status']=='completed':
    assert len(report['folds'])==3 and all(set(f['arms'])=={'state','history','both'} and 'positive_state_signal' in f for f in report['folds'])
for path,digest in contract['bindings'].items():
    assert sha(path)==digest,path
config=read('logs/roadmap/joint-professional-fit-05/configuration.json')
paths=[Path(s['dataset']) for s in config['sources'] if s['role']=='teaching']
assert sorted(p.name for p in paths)==sorted(g for f in contract['folds'] for g in f)
games={}
for path in paths:
    static=read(path/'static.json')['game_data']
    pairs=[]
    labels=[]
    for inputs,label,command,reason in replay_examples(path,*contract['vocabulary'],DELAYS,construction_products(static),spatial=False,missing_fields=True):
        pairs.append(probe_features(inputs,*contract['vocabulary'][:2]))
        labels.append(command.ability)
    games[path.name]=dict(state=vstack([p[0] for p in pairs]).tocsr(),history=vstack([p[1] for p in pairs]).tocsr(),labels=np.array(labels))
    assert len(labels)==report['preparation'][path.name]['rows']
    print(json.dumps(dict(stage='reconstructed',game=path.name,rows=len(labels))),flush=True)
macro_ids=sorted(a['ability_id'] for a in static['abilities'] if any(k in a.get('friendly_name','').upper() for k in ('BUILD ','TRAIN ','RESEARCH ')))
assert macro_ids==report['macro_ids']
audit=[]
for number,fold in enumerate(report['folds']):
    held=contract['folds'][number]
    train=[p.name for p in paths if p.name not in held]
    assert fold['held']==held and fold['train']==train
    training_labels=np.concatenate([games[g]['labels'] for g in train])
    labels=np.concatenate([games[g]['labels'] for g in held])
    classes,counts=np.unique(training_labels,return_counts=True)
    for arm,entry in fold['arms'].items():
        def matrix(game):
            return hstack([games[game]['state'],games[game]['history']]).tocsr() if arm=='both' else games[game][arm]
        training=vstack([matrix(g) for g in train]).tocsr()
        validation=vstack([matrix(g) for g in held]).tocsr()
        binding=fold['models'][arm]
        assert sha(binding['path'])==binding['sha256']
        with np.load(binding['path'],allow_pickle=False) as archive:
            model={k:archive[k] for k in archive.files}
        assert all(np.isfinite(x).all() for x in model.values())
        np.testing.assert_array_equal(model['classes'],classes)
        squares=np.asarray(training.power(2).mean(axis=0)).ravel()
        np.testing.assert_array_equal(model['columns'],np.flatnonzero(squares))
        np.testing.assert_allclose(model['scales'],np.sqrt(squares[model['columns']]),rtol=0,atol=0)
        def logits(x):
            return x[:,model['columns']].multiply(1/model['scales']) @ model['weights']+model['bias']
        predicted=classes[logits(validation).argmax(axis=1)]
        assert predicted.tolist()==fold['predictions'][arm]
        assert metrics(logits(validation),classes,labels,macro_ids)==entry['metrics']
        for g in held:
            assert metrics(logits(matrix(g)),classes,games[g]['labels'],macro_ids)==entry['per_game'][g]
        assert entry['fit']['class_counts']=={str(c):int(n) for c,n in zip(classes,counts,strict=True)}
        assert entry['fit']['samples']==len(training_labels) and entry['fit']['iterations']<=100
        assert entry['fit']['active_columns']==len(model['columns'])
    baseline=np.tile(np.log(counts/counts.sum()),(len(labels),1))
    if fold['arms']:
        assert metrics(baseline,classes,labels,macro_ids)==fold['baseline']
    else:
        assert fold['baseline']=={} and report['status']=='wall_bound_inconclusive'
    if set(fold['arms'])=={'state','history','both'}:
        s,h=(fold['arms'][a] for a in ['state','history'])
        sm,hm,b=s['metrics'],h['metrics'],fold['baseline']
        positive=bool(s['fit']['status']==h['fit']['status']=='converged' and sm['macro_exact_recall']>=.25 and sm['macro_exact_recall']>=hm['macro_exact_recall']+.1 and sm['macro_exact_recall']>=b['macro_exact_recall']+.1 and sm['macro_false_positive_rate']<=.1)
        if 'positive_state_signal' in fold:
            assert positive==fold['positive_state_signal']
        else:
            assert report['status']=='wall_bound_inconclusive'
    if 'state' in fold['predictions']:
        offset=0
        for g in held:
            predicted=np.array(fold['predictions']['state'][offset:offset+len(games[g]['labels'])])
            failed=np.flatnonzero(np.isin(games[g]['labels'],macro_ids) & (predicted!=games[g]['labels']))[:3]
            with gzip.open(next(p for p in paths if p.name==g)/'examples.jsonl.gz','rt') as stream:
                source=list(map(json.loads,stream))
            for index in failed:
                row=source[index]
                obs=row['observation']
                assert len(row['commands'])==1 and row['commands'][0]['ability']==int(games[g]['labels'][index])
                own=[u for u in obs['units'] if u['alliance']==1]
                audit.append(dict(game=g,index=int(index),action_loop=row['action_loop'],gold_ability=int(games[g]['labels'][index]),predicted_ability=int(predicted[index]),player=obs['player'],unknown_fields=obs.get('unknown_fields',{}),own_types=dict(Counter(u['unit_type'] for u in own)),own_build_progress=[dict(unit_type=u['unit_type'],build_progress=u.get('build_progress'),orders=u.get('orders')) for u in own if u.get('build_progress',1)<1 or u.get('orders')],scope='Recorded pre-effect partial source only; native legality/prerequisites are not proved.'))
            offset+=len(games[g]['labels'])
assert report['positive_state_signal']==(report['status']=='completed' and sum(f.get('positive_state_signal',False) for f in report['folds'])>=2)
telemetry=read('logs/roadmap/intention-probe-01.telemetry.json')
assert telemetry['status']=='completed' and telemetry['returncode']==0 and telemetry['stop_reason'] is None
result=dict(status='verified_signal_diagnostic',positive_state_signal=report['positive_state_signal'],report_sha256=sha(OUT/'report.json'),contract_sha256=sha(OUT/'contract.json'),verifier_sha256=sha(__file__),telemetry_sha256=sha('logs/roadmap/intention-probe-01.telemetry.json'),reconstructed_rows=sum(g['labels'].size for g in games.values()),audited_failed_macro_rows=audit,scope='Models/metrics/scaling/source folds verified; no solver refit, reserved predictions, native games, or competence claim.')
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],positive_state_signal=result['positive_state_signal'],audited_rows=len(audit))),flush=True)
