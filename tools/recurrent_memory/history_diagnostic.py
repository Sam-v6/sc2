"""Training-only temporal-information check; no policy updates or native games."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np


def samples(encoded, chosen, episodes, observed, horizon=8, lags=(1,4,8), actions=27):
    rows, labels, ids=[],[],[]
    onehot=np.eye(actions)[chosen]
    for episode in np.unique(episodes):
        indices=np.flatnonzero(episodes==episode)
        assert np.all(np.diff(indices)==1)
        start,end=indices[0],indices[-1]+1
        for current in range(start+max(lags)+1,end-horizon):
            blocks=[]
            for lag in (0,*lags):
                i=current-lag
                blocks.append(np.concatenate([encoded[i],onehot[i-1]]))
            rows.append(blocks)
            labels.append(observed[current+horizon])
            ids.append(episode)
    ordered=np.asarray(rows)
    shuffled=ordered.copy()
    rng=np.random.default_rng(331)
    for row in shuffled:
        row[1:]=row[1:][rng.permutation(len(lags))]
    return {'current':ordered[:,0], 'ordered':ordered.reshape(len(rows),-1),
            'shuffled':shuffled.reshape(len(rows),-1)},np.asarray(labels),np.asarray(ids)


def predict(train, targets, test, penalty=1):
    mean,std=train.mean(axis=0),train.std(axis=0)
    std=np.maximum(std,1e-8)
    x=np.column_stack([np.ones(len(train)),(train-mean)/std])
    z=np.column_stack([np.ones(len(test)),(test-mean)/std])
    regularizer=np.eye(x.shape[1])*penalty
    regularizer[0,0]=0
    coefficients=np.linalg.solve(x.T@x+regularizer,x.T@targets)
    return z@coefficients


def load_archive(path):
    with np.load(path,allow_pickle=False) as archive:
        return {key:archive[key] for key in archive.files}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(output):
    from src.rl.actor_critic import ActorCritic
    from src.rl.terran import ACTIONS,FEATURES
    assert not output.exists()
    corpus=Path('logs/self-imitation/training-corpus.npz').resolve()
    parent=Path('logs/ppo-combat-kills/frozen-easy40.npz').resolve()
    audit=Path('logs/audit/self-imitation-gradient-independent-review.json').resolve()
    before=digest(audit)
    review=json.loads(audit.read_text())
    assert review['passed']
    inherited={**review['data_hashes'],**review.get('source_hashes',{})}
    for path,expected in inherited.items():
        assert digest(path)==expected,path
    assert inherited[str(corpus)]==digest(corpus)
    assert inherited[str(parent)]==digest(parent)
    hashes={**inherited,str(audit):before}
    paths=[Path(__file__).resolve(),Path(__file__).with_name('test_history_diagnostic.py').resolve(),
           Path('docs/superpowers/plans/2026-10-05-history-diagnostic.md').resolve()]
    for path in paths:
        assert str(path) not in hashes
        hashes[str(path)]=digest(path)
    policy=ActorCritic.load(parent,FEATURES,ACTIONS)
    data=load_archive(corpus)
    print(json.dumps({"stage":"loaded","rows":len(data["chosen"])}),flush=True)
    metadata=json.loads(str(data['metadata']))
    assert metadata['features']==FEATURES and metadata['actions']==ACTIONS
    assert len(metadata['episodes'])==80
    width=len(FEATURES)
    encoded=[];observed=[]
    columns=[FEATURES.index(key) for key in ['enemy_near_base','enemy_near_army','idle_barracks','idle_townhalls']]
    for start in range(0,len(data['chosen']),256):
        end=min(start+256,len(data['chosen']))
        states=np.zeros((end-start,width))
        for offset,row in enumerate(range(start,end)):
            a,b=data['indptr'][row:row+2]
            states[offset,data['indices'][a:b]]=data['values'][a:b]
        encoded.append(np.tanh(states@policy.network[0]+policy.network[1]))
        observed.append(np.column_stack([(states[:,columns[:2]]>0).any(axis=1),
                                         (states[:,columns[2:]]>0).any(axis=1)]))
    blocks,labels,episodes=samples(np.concatenate(encoded),data['chosen'],data['episode'],np.concatenate(observed))
    test=episodes%4==0
    assert not set(episodes[test]) & set(episodes[~test])
    scores={}
    for name,features in blocks.items():
        print(json.dumps({'stage':'fit_predictor','control':name}),flush=True)
        predictions=np.clip(predict(features[~test],labels[~test],features[test]),0,1)
        errors=(predictions-labels[test])**2
        scores[name]={'brier':errors.mean(axis=0).tolist(),'mean_brier':float(errors.mean()),
                      'episode_brier':{int(ep):errors[episodes[test]==ep].mean(axis=0).tolist() for ep in np.unique(episodes[test])}}
    current,ordered,shuffled=[scores[key]['mean_brier'] for key in ['current','ordered','shuffled']]
    checks={'ordered_at_least_2_percent_better_than_current':ordered<=current*.98,
            'ordered_at_least_half_percent_better_than_shuffled':ordered<=shuffled*.995,
            'neither_target_regresses':all(a<=b for a,b in zip(scores['ordered']['brier'],scores['current']['brier']))}
    for path,expected in hashes.items():
        assert digest(path)==expected,path
    result={'passed_information_gate':all(checks.values()),'checks':checks,'scores':scores,
            'targets':['observed_enemy_near_base_or_army_at_t_plus_8','idle_barracks_or_townhalls_at_t_plus_8'],
            'train_episodes':sorted(map(int,np.unique(episodes[~test]))),'heldout_episodes':sorted(map(int,np.unique(episodes[test]))),
            'train_rows':int((~test).sum()),'heldout_rows':int(test.sum()),'horizon_decisions':8,'lags':[1,4,8],
            'ridge_penalty':1,'shuffle_seed':331,'data_hashes':hashes,'optimizer_updates':0,'games_launched':0,
            'scope':'Training-only temporal prediction evidence; no recurrent policy training or gameplay strength claim.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as file:
        json.dump(result,file,indent=2,allow_nan=False);file.write('\n')
    print(json.dumps({key:result[key] for key in ['passed_information_gate','checks','train_rows','heldout_rows']}),flush=True)


if __name__=='__main__':
    run(Path(sys.argv[1]))
