"""Fixed case exposure and development gates; no checkpoint fitting decisions."""
import numpy as np
ROLES=['recurrent','reset','reference']


def case(index,seed,phase,difficulty,mode,training=False):
    return {'seed':seed,'policy_seed':seed,'phase':phase,'difficulty':difficulty,'mode':mode,
            'race':('Terran','Protoss','Zerg')[index%3],
            'build':('Rush','Timing','Power','Macro','Air')[index%5],
            'map':('Simple64','TritonLE')[(index//2 if training else index)%2]}


def training_cases():
    return [case(i,121000+i,'train','Medium' if i%2==0 else 'Hard','train',True) for i in range(64)]


def evaluation_cases():
    bank=[]
    for phase,start,count,difficulty,mode in [('hard_greedy',122000,12,'Hard','evaluate'),
                                           ('hard_sampled',123000,12,'Hard','sample'),
                                           ('easy_sampled',124000,6,'Easy','sample')]:
        bank.extend(case(i,start+i,phase,difficulty,mode) for i in range(count))
    return bank


def gate(rows):
    bank=evaluation_cases();expected={(x['seed'],role) for x in bank for role in ROLES}
    assert len(rows)==90 and {(r['seed'],r['role']) for r in rows}==expected
    panels={};gains={}
    for phase in ['hard_greedy','hard_sampled','easy_sampled']:
        panels[phase]={};gains[phase]={}
        for role in ROLES:
            selected=[];pairs=[]
            for c in [x for x in bank if x['phase']==phase]:
                row=next(r for r in rows if r['seed']==c['seed'] and r['role']==role)
                ref=next(r for r in rows if r['seed']==c['seed'] and r['role']=='reference')
                assert all(row[key]==value for key,value in c.items())
                assert row['result'] in ['Victory','Defeat','Tie'] and np.isfinite(row['discounted_return'])
                selected.append(row);pairs.append({'seed':c['seed'],'race':c['race'],
                    'win_gain':int(row['result']=='Victory')-int(ref['result']=='Victory'),
                    'return_gain':row['discounted_return']-ref['discounted_return'],
                    'reference_result':ref['result'],'result':row['result']})
            panels[phase][role]={'wins':sum(r['result']=='Victory' for r in selected),
                                'mean_return':float(np.mean([r['discounted_return'] for r in selected]))}
            gains[phase][role]={'wins':sum(p['win_gain'] for p in pairs),
                'mean_return':float(np.mean([p['return_gain'] for p in pairs])),
                'race_means':{race:float(np.mean([p['return_gain'] for p in pairs if p['race']==race])) for race in ['Terran','Protoss','Zerg']},
                'lost_reference_wins':[p['seed'] for p in pairs if p['reference_result']=='Victory' and p['result']!='Victory']}
    supported={}
    for role in ['recurrent','reset']:
        greedy,sampled,easy=[gains[p][role] for p in ['hard_greedy','hard_sampled','easy_sampled']]
        supported[role]=(greedy['wins']>=2 and greedy['mean_return']>.02 and min(greedy['race_means'].values())>=0
                         and sampled['wins']>=0 and sampled['mean_return']>=0 and easy['wins']>=0 and easy['mean_return']>=-.02)
    valid=[role for role in ['reset','recurrent'] if supported[role]]
    key=lambda role:(panels['hard_greedy'][role]['wins'],panels['hard_sampled'][role]['wins'],panels['hard_greedy'][role]['mean_return'])
    chosen=max(valid,key=key) if valid else None
    memory=supported['recurrent'] and all(panels[p]['recurrent']['wins']>=panels[p]['reset']['wins']+2
                 and panels[p]['recurrent']['mean_return']>=panels[p]['reset']['mean_return'] for p in ['hard_greedy','hard_sampled'])
    return {'supported':supported,'selected_role':chosen,'memory_advantage':memory,'panels':panels,'gains_vs_reference':gains,
            'scope':'Development support only; final all-race Hard acceptance remains separate.'}
