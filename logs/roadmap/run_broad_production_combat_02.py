"""Frozen all-race native execution fixture, no model decisions or training."""
import hashlib,json,math,threading
from pathlib import Path
import psutil
from src.learning import entity_play
from src.learning.entity_play import JointImitationBot
from src.learning.gameplay import Command
from src.runtime import supervise
OUT=Path('logs/roadmap/broad-production-combat-02')

class ScriptedRequestFixture(JointImitationBot):
    async def on_start(self):
        await super().on_start()
        self.agent.decide=self.fixture_decision

    def fixture_decision(self,state,candidates=None):
        loop=state['game_loop']
        if loop<self.agent.next_loop:
            return None,None
        own=[u for u in state['units'] if u['alliance']==1]
        workers=[u for u in own if u['unit_type']==45]
        bases=[u for u in own if u['unit_type']==18 and not u.get('orders',[])]
        barracks=[u for u in own if u['unit_type']==21]
        minerals=state['player']['minerals']
        food=state['player']['food_cap']-state['player']['food_used']
        # Fixture priorities are declared scripted, not inferred from a model.
        if len(workers)<16 and bases and minerals>=50 and food>=1:
            return Command(524,(bases[0]['tag'],)),44
        depots=[u for u in own if u['unit_type'] in (19,47) and u.get('build_progress',1)==1]
        protected=self.scout.protected | (set(self.supply_pending[0].units) if self.supply_pending else set())
        free=[u for u in workers if u['tag'] not in protected and all(o['ability_id'] in (295,3666) for o in u.get('orders',[]))]
        if depots and free and minerals>=150 and len(barracks)<(1 if len(workers)<20 else 4):
            origin=tuple(self.start_location.towards(self.game_info.map_center,16))
            dx,dy=self.game_info.map_center.x-self.start_location.x,self.game_info.map_center.y-self.start_location.y
            distance=math.hypot(dx,dy);offset=(0,6,-6,12)[len(barracks)]
            point=(origin[0]-dy/distance*offset,origin[1]+dx/distance*offset)
            worker=min(free,key=lambda u:(math.dist(u['position'][:2],point),u['tag']))
            return Command(321,(worker['tag'],),target_point=point),44
        if len(workers)<20 and bases and minerals>=50 and food>=1:
            return Command(524,(bases[0]['tag'],)),44
        ready=[u for u in barracks if u.get('build_progress',1)==1 and not u.get('orders',[])]
        count=min(len(ready),minerals//50,food)
        if count:
            return Command(560,tuple(u['tag'] for u in ready[:count])),44
        self.agent.next_loop=loop+8
        return None,None


def play_fixture(job):
    original=entity_play.JointImitationBot
    entity_play.JointImitationBot=ScriptedRequestFixture
    try:
        result=entity_play.play_joint_job(job)
    finally:
        entity_play.JointImitationBot=original
    result.update(controller='scripted_request_execution_fixture',
                  fixture_commands=result['commands'],learned_commands=0,
                  checkpoint_predictions_used=False,learned_competence=False)
    Path(job['output'],'episode.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    OUT.mkdir(exist_ok=False)
    model=Path('logs/roadmap/joint-professional-fit-05/policy.npz')
    paths=[Path(__file__),model,Path('src/runtime.py'),Path('src/runner.py'),Path('src/bots/terran_primitives.py')]
    paths.extend(Path('src/learning').glob('*.py'))
    bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    jobs=[dict(controller='joint',policy=str(model.resolve()),primitive_assistance=True,reactive_supply=True,
        engine_placement=True,wait_unavailable=True,max_game_step=8,map='AcropolisLE',race=race,
        difficulty='VeryEasy',build='Macro',seed=823221+i,seconds=600,
        output=str((OUT/race).resolve())) for i,race in enumerate(('Terran','Zerg','Protoss'))]
    (OUT/'contract.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,training=False,rl=False,
        engineering_only=True,cpu_limit=80,wall_seconds_per_game=180,
        gates=dict(worker_births=8,marine_births=40,barracks_completions=4,damage_dealt=1,
                   killed_value=1,army_distance_from_start=25,raw_delayed_errors=0),
        fixture='20 SCVs, four Barracks, continuous Marines; supply/scouting/combat explicitly scripted',
        limits=['No checkpoint predictions; loaded only for adapter engine-vocabulary setup.',
                'All request history is fixture provenance, not learned decisions.',
                'This checks native execution, not Hard strength or learned competence.']),indent=2)+'\n')
    assert psutil.cpu_percent(interval=1)<70
    done,stop=threading.Event(),threading.Event();samples=[]
    def watch():
        high=0
        while not done.is_set():
            cpu=psutil.cpu_percent(interval=1);samples.append(cpu);high=high+1 if cpu>80 else 0
            if high>=3:stop.set()
            done.wait(1)
    watcher=threading.Thread(target=watch,daemon=True);watcher.start();results=[]
    try:
        for job in jobs:
            if stop.is_set():break
            result=supervise(play_fixture,(job,),180,stop_event=stop);results.append(result)
            print(json.dumps({k:result.get(k) for k in ('status','result','race','fixture_commands','score','error','wall_seconds')}),flush=True)
            if result['status'] not in ('completed','truncated'):break
    finally:done.set();watcher.join(3)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
    for p in paths:
        dest=OUT/'source-snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    (OUT/'report.json').write_text(json.dumps(dict(status='completed' if len(results)==3 and all(r['status'] in ('completed','truncated') for r in results) else 'failed',results=results,
        peak_cpu=max(samples,default=0),samples=samples,bindings=bindings,training=False,rl=False),indent=2)+'\n')
if __name__=='__main__':main()
