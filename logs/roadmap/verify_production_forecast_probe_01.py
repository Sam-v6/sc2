"""Reload diagnostic artifacts and reconstruct labels, primal scores and metrics."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz, hstack
out=Path('logs/roadmap/production-forecast-probe-01')
report=json.loads((out/'report.json').read_text())
for p,d in report['bindings'].items():
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==d,p
assert report['rl'] is False and report['controller'] is False
labels={r:np.load(out/f'{r}-labels.npy',allow_pickle=False) for r in ('teaching','development')}
matrices={r:{f:load_npz(out/f'{r}-{f}.npz') for f in ('state','history')} for r in labels}
games={}
for c in report['coverage']:
    g=c['game']; role=c['role']
    root=Path('logs/roadmap')/('pro-demonstrations-production-08' if role=='teaching' else 'pro-demonstrations-07')/g
    with gzip.open(root/'examples.jsonl.gz','rt') as stream:
        rows=list(map(json.loads,stream))
    receipt=json.loads((root/'dataset.json').read_text())
    unresolved={(x['event']['_gameloop'],x['event']['m_sequence']) for x in receipt['issued_command_audit']['unresolved_events']}
    data=json.loads((root/'static.json').read_text())['game_data']
    names={a['ability_id']:a.get('friendly_name','') for a in data['abilities']}
    prod={a for a,n in names.items() if n.startswith(('Build ','Train ','Research '))}
    prod|={u['ability_id'] for u in data['units'] if 8 in u.get('attributes',[]) and names.get(u.get('ability_id'),'').startswith('Morph')}
    games[g]=(rows,unresolved,prod)
verified_labels=0
for role,truth in labels.items():
    refs=json.loads((out/f'{role}-rows.json').read_text())
    assert len(refs)==len(truth)
    for ref,label in zip(refs,truth,strict=True):
        rows,unresolved,prod=games[ref['game']]
        current=rows[ref['row']]; key=(current['action_loop'],current['source_sequence'])
        target=next(r for r in rows[ref['row']:] if r['commands'][0]['ability'] in prod)
        targetkey=(target['action_loop'],target['source_sequence'])
        assert list(targetkey)==ref['target_key']
        assert not any(key<u<targetkey for u in unresolved)
        np.testing.assert_array_equal(label,[target['commands'][0]['ability'],(targetkey[0]-key[0])/22.4])
        verified_labels+=1

def check_metrics(truth,pred,expected):
    for subset,mask in [('all',np.ones(len(truth),dtype=bool)),('positive_delay',truth[:,1]>0),('nonworker',truth[:,0]!=524)]:
        t=truth[mask]; p=pred[mask]; result=expected[subset]
        assert result['rows']==len(t)
        recalls=[]
        for c in np.unique(t[:,0]):
            keep=t[:,0]==c
            correct=int((p[keep,0]==c).sum())
            assert result['classes'][str(int(c))]['rows']==int(keep.sum())
            assert result['classes'][str(int(c))]['correct']==correct
            recalls.append(correct/keep.sum())
        np.testing.assert_allclose([result['accuracy'],result['macro_recall'],result['delay_mae']],[(t[:,0]==p[:,0]).mean(),np.mean(recalls),np.abs(t[:,1]-p[:,1]).mean()],rtol=1e-12,atol=1e-12)
majority=Counter(labels['teaching'][:,0]).most_common(1)[0][0]
mean=labels['teaching'][:,1].mean()
for role,truth in labels.items():
    check_metrics(truth,np.column_stack([np.full(len(truth),majority),np.full(len(truth),mean)]),report['baseline'][role])
verified_predictions=0
for feature in ('state','state_history'):
    model=dict(np.load(out/f'{feature}-model.npz',allow_pickle=False))
    teaching=load_npz(out/f'{feature}-training-values.npz')
    # Reconstruct an equivalent primal affine predictor instead of calling predict_forecast.
    weights=teaching.T@model['dual']
    teaching_mean=np.asarray(teaching.mean(axis=0)).ravel()
    for role,truth in labels.items():
        m=matrices[role]
        x=m['state'] if feature=='state' else hstack([m['state'],m['history']]).tocsr()
        squares=np.asarray((matrices['teaching']['state'] if feature=='state' else hstack([matrices['teaching']['state'],matrices['teaching']['history']]).tocsr()).power(2).mean(axis=0)).ravel()
        np.testing.assert_array_equal(model['columns'],np.flatnonzero(squares))
        np.testing.assert_allclose(model['scales'],np.sqrt(squares[model['columns']]))
        values=x[:,model['columns']].multiply(1/model['scales']).tocsr()
        scores=values@weights-teaching_mean@weights+model['prior']
        pred=np.column_stack([model['classes'][scores[:,:-1].argmax(axis=1)],np.maximum(0,np.expm1(scores[:,-1]))])
        saved=np.load(out/f'{feature}-{role}-predictions.npy',allow_pickle=False)
        np.testing.assert_array_equal(pred[:,0],saved[:,0])
        np.testing.assert_allclose(pred[:,1],saved[:,1],rtol=1e-8,atol=1e-8)
        check_metrics(truth,saved,report['models'][feature]['metrics'][role])
        verified_predictions+=len(pred)
result=dict(status='verified',labels=verified_labels,predictions=verified_predictions,report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
