"""Record scripted demonstrations through the unchanged learner executor."""
import json
from pathlib import Path
import numpy as np
import selector
from selector import TeacherPolicy
from recurrent_worker import JournalLearner,digest
from src.rl import train as ordinary
from src.rl.actor_critic import ActorCritic
from src.rl.terran import ACTIONS,FEATURES


class ObservedLearner(JournalLearner):
    def __init__(self,*args,production,commands,**kwargs):
        super().__init__(*args,**kwargs)
        self.production=Path(production);self.commands=Path(commands)
        self.production_file=self.production.open('x',buffering=1)
        self.command_file=self.commands.open('x',buffering=1)

    def observed(self,event,unit):
        self.production_file.write(json.dumps({'event':event,'time':self.time,'tag':unit.tag,'type':unit.type_id.name})+'\n')

    async def custom_on_step(self,iteration):
        await super().custom_on_step(iteration)
        queued=[]
        for command in self.actions:
            target=command.target
            if hasattr(target,'tag'):target={'unit_tag':target.tag}
            elif target is not None:target={'position':list(target)}
            queued.append({'unit':command.unit.tag,'ability':command.ability.name,'target':target,'queue':command.queue})
        self.command_file.write(json.dumps({'time':self.time,'decision_index':len(self.decisions)-1,'queued':queued})+'\n')

    async def on_unit_created(self,unit):self.observed('unit_appeared',unit)
    async def on_building_construction_complete(self,unit):self.observed('building_completed',unit)


def entrypoint_probe():return {'file':__file__,'games_launched':0}


def episode(job):
    assert job['purpose']=='macro-teacher-preflight' and job['mode']=='evaluate'
    assert job['game_limit']==1200 and job['macro_seconds']==1
    assert digest(job['behavior_checkpoint'])==job['behavior_checkpoint_sha256']
    assert job['checkpoint_role']=='context_only_not_teacher_weights'
    assert job['teacher_source']==str(Path(selector.__file__).resolve()) and digest(job['teacher_source'])==job['teacher_source_sha256']
    for key in ['actions','journal','replay','trajectory','production','commands']:
        path=Path(job[key]);assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True)
    context=ActorCritic.load(job['behavior_checkpoint'],FEATURES,ACTIONS)
    policy=TeacherPolicy(context)
    for key in ['gamma','reward_scale','reward_version','macro_seconds']:assert getattr(policy,key)==job[key]
    bots=[]
    def load(path,features,actions):
        assert str(path)==job['behavior_checkpoint'] and features==FEATURES and actions==ACTIONS
        return policy
    def bot(*args,**kwargs):
        instance=ObservedLearner(*args,journal=job['journal'],production=job['production'],commands=job['commands'],**kwargs)
        bots.append(instance);return instance
    previous_load,previous_bot=ordinary.load_policy,ordinary.TerranLearner
    ordinary.load_policy,ordinary.TerranLearner=load,bot
    try:result=ordinary.episode(job)
    finally:
        ordinary.load_policy,ordinary.TerranLearner=previous_load,previous_bot
        for instance in bots:instance.production_file.close();instance.command_file.close()
    assert len(bots)==1 and result['updates_before']==result['updates_after']==0
    assert digest(job['behavior_checkpoint'])==job['behavior_checkpoint_sha256']
    assert digest(job['teacher_source'])==job['teacher_source_sha256']
    transitions=bots[0].transitions;assert transitions and transitions[-1][-1] and not any(t[-1] for t in transitions[:-1])
    data={'states':np.array([t[0] for t in transitions]),'chosen':np.array([t[1] for t in transitions]),
          'legal':np.array([[a in row['legal'] for a in ACTIONS] for row in bots[0].decisions]),
          'rewards':np.array([t[2] for t in transitions]),'terminal':np.array([t[-1] for t in transitions])}
    meta={**job,'algorithm':policy.algorithm,'features':FEATURES,'actions_schema':ACTIONS,'result':result['result'],
          'on_policy_ppo_reuse_allowed':False,'scripted_macro':True}
    with Path(job['trajectory']).open('xb') as file:np.savez_compressed(file,metadata=np.array(json.dumps(meta)),**data)
    result.update(trajectory_sha256=digest(job['trajectory']),trajectory_rows=len(transitions),
                  journal_bytes=Path(job['journal']).stat().st_size,production_bytes=Path(job['production']).stat().st_size,command_bytes=Path(job['commands']).stat().st_size)
    return result
