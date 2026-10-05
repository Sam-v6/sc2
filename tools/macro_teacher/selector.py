"""Scripted training teacher; this selector never executes game commands."""
import numpy as np
from src.rl.terran import ACTIONS,FEATURES,SCALES

INDICES={name:FEATURES.index(name) for name in SCALES}


def choose(state,mask):
    assert state.shape==(len(FEATURES),) and mask.shape==(len(ACTIONS),) and mask.dtype==bool
    assert np.isfinite(state).all() and mask[0]
    s={name:float(state[index]*SCALES[name]) for name,index in INDICES.items()}
    army,bases=s['army'],max(1,s['bases'])
    priority=[]
    if s['supply_left']<max(4,min(12,army*.12)):priority.append('depot')
    if not s['attacking'] and army>=32 and not s['enemy_near_base']:priority.append('attack')
    if s['attacking'] and army<10 and s['enemy_near_base']:priority.append('retreat')
    priority.append('orbital')
    if s['workers']<min(66,22*bases):priority.append('scv')
    if s['barracks']<1:priority.append('barracks')
    if s['refinery']<min(4,2*bases):priority.append('refinery')
    if bases<2 and army>=10 and not s['enemy_near_base']:priority.append('expand')
    if bases<3 and army>=40 and s['workers']>=40 and not s['enemy_near_base']:priority.append('expand')
    if s['barracks']<min(6,2*bases) and army>=6:priority.append('barracks')
    if s['factory']<1 and army>=6:priority.append('factory')
    if s['starport']<1 and army>=12:priority.append('starport')
    priority.extend(['factory_techlab','barracks_techlab'])
    if s['engineeringbay']<1 and army>=12:priority.append('engineeringbay')
    priority.append('infantry_weapons')
    if s['enemy_cloaked']:
        priority.append('starport_techlab')
        if s['ravens']<1:priority.append('raven')
        if s['turrets']<2:priority.append('turret')
    if s['enemy_air']>s['vikings']*2 and s['vikings']<4:priority.append('viking')
    if s['medivacs']<max(2,min(4,army/16)):priority.append('medivac')
    if s['tanks']<max(2,min(4,army/12)):priority.append('tank')
    if s['marauders']<max(4,s['marines']/4):priority.append('marauder')
    priority.extend(['marine','wait'])
    return next(ACTIONS.index(name) for name in priority if mask[ACTIONS.index(name)])


class TeacherPolicy:
    algorithm='macro-teacher-v1'
    updates=0
    epsilon=0

    def __init__(self,context):
        self.features=FEATURES;self.actions=ACTIONS
        for key in ['gamma','reward_scale','reward_version','macro_seconds']:
            setattr(self,key,getattr(context,key))

    def act(self,state,mask,explore=False):return choose(state,mask)
