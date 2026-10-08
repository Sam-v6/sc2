"""Learned residual recurrent PPO with frozen parent and explicit episode state.

NumPy serves games; Torch is imported only by the CPU trainer. Whole episodes
are minibatches, so sequence likelihoods are reconstructed from episode start.
"""
import json
from pathlib import Path
import numpy as np
from recurrent_core import RecurrentCore
from src.rl.actor_critic import ActorCritic

NAMES=['weight_ih','weight_hh','bias_ih','bias_hh','actor','value']


def discounted_returns(rewards,gamma):
    returns=np.zeros(len(rewards));carry=0.
    for index in reversed(range(len(rewards))):
        carry=float(rewards[index])+gamma*carry;returns[index]=carry
    return returns


def probabilities(logits,mask):
    mask=np.asarray(mask,dtype=bool)
    assert mask.any(axis=-1).all()
    logits=np.where(mask,logits,-np.inf)
    weights=np.exp(logits-np.max(logits,axis=-1,keepdims=True))
    return weights/weights.sum(axis=-1,keepdims=True)


class RecurrentPolicy:
    algorithm='recurrent-ppo-v1'
    settings={'epochs':4,'learning_rate':.0003,'clip':.2,'entropy':.01,
              'value':.5,'max_grad_norm':.5,'eps':1e-5,'minibatch':'whole-episode',
              'parent_frozen':True}

    def __init__(self,parent,seed,memory_reset):
        self.features,self.actions=list(parent.features),list(parent.actions)
        self.core=RecurrentCore(parent,seed)
        self.gamma,self.reward_scale=parent.gamma,parent.reward_scale
        self.macro_seconds,self.reward_version=parent.macro_seconds,parent.reward_version
        self.parent_updates=parent.updates
        self.memory_reset=bool(memory_reset)
        self.rng=np.random.default_rng(seed)
        self.m,self.v=[[np.zeros_like(p) for p in self.parameters()] for _ in range(2)]
        self.updates=self.episodes=self.attempts=0
        self.epsilon=0
        self.reset_episode()

    def parameters(self):
        return [getattr(self.core,name) for name in NAMES]

    def reset_episode(self):
        self.memory=(np.zeros(32),-1)
        self.trace=[]

    def step(self,state,memory):
        if self.memory_reset:
            memory=(np.zeros(32),memory[1])
        return self.core.step(state,memory)

    def act(self,state,mask,explore):
        logits,value,hidden=self.step(state,self.memory)
        probs=probabilities(logits,mask)
        action=int(self.rng.choice(len(self.actions),p=probs)) if explore else int(probs.argmax())
        self.trace.append({'action':action,'logp':float(np.log(probs[action])),'value':float(value)})
        self.memory=(hidden,action)
        return action

    def sequence(self,states,chosen):
        memory=(np.zeros(32),-1)
        logits,values=[],[]
        for state,action in zip(states,chosen):
            logit,value,hidden=self.step(state,memory)
            logits.append(logit);values.append(value)
            memory=(hidden,int(action))
        return np.asarray(logits),np.asarray(values)

    def episode(self,states,chosen,masks,rewards):
        assert len(states)==len(chosen)==len(masks)==len(rewards)==len(self.trace)>0
        chosen=np.asarray(chosen,dtype=int)
        assert np.array_equal(chosen,[row['action'] for row in self.trace])
        assert np.asarray(masks)[np.arange(len(chosen)),chosen].all()
        logits,values=self.sequence(states,chosen)
        logp=np.log(probabilities(logits,masks)[np.arange(len(chosen)),chosen])
        np.testing.assert_allclose(logp,[row['logp'] for row in self.trace],rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(values,[row['value'] for row in self.trace],rtol=1e-12,atol=1e-12)
        returns=discounted_returns(rewards,self.gamma)
        terminal=np.zeros(len(rewards),dtype=bool);terminal[-1]=True
        return {'states':np.asarray(states),'chosen':chosen,'legal':np.asarray(masks,dtype=bool),
                'rewards':np.asarray(rewards),'logp':logp,'values':values,
                'returns':returns,'advantages':returns-values,'terminal':terminal}

    def save(self,path):
        path=Path(path);assert not path.exists()
        metadata={'algorithm':self.algorithm,'features':self.features,'actions':self.actions,
                  'settings':self.settings,'gamma':self.gamma,'reward_scale':self.reward_scale,
                  'reward_version':self.reward_version,'macro_seconds':self.macro_seconds,
                  'parent_updates':self.parent_updates,'memory_reset':self.memory_reset,
                  'updates':self.updates,'episodes':self.episodes,'attempts':self.attempts,
                  'rng':self.rng.bit_generator.state,'previous':self.memory[1],'trace':self.trace}
        arrays={'metadata':np.array(json.dumps(metadata)),'hidden':self.memory[0]}
        for group,values in [('network',self.core.network),('parameters',self.parameters()),('m',self.m),('v',self.v)]:
            arrays.update({f'{group}{i}':value for i,value in enumerate(values)})
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as file:
            np.savez_compressed(file,**arrays)

    @classmethod
    def load(cls,path,features,actions):
        with np.load(path,allow_pickle=False) as archive:
            meta=json.loads(str(archive['metadata']))
            assert meta['algorithm']==cls.algorithm and meta['settings']==cls.settings
            assert meta['features']==list(features) and meta['actions']==list(actions)
            assert np.isfinite(meta['gamma']) and 0<meta['gamma']<1
            assert meta['reward_scale']==.01 and meta['reward_version']=='combat-kills-v1' and meta['macro_seconds']==1
            assert type(meta['memory_reset']) is bool
            for name in ['updates','episodes','attempts','parent_updates']:
                assert type(meta[name]) is int and meta[name]>=0
            assert meta['episodes']<=meta['attempts']
            assert type(meta['previous']) is int and -1<=meta['previous']<len(actions)
            assert isinstance(meta['trace'],list)
            for row in meta['trace']:
                assert type(row['action']) is int and 0<=row['action']<len(actions)
                assert np.isfinite(row['logp']) and row['logp']<=0 and np.isfinite(row['value'])
            assert meta['previous']==(meta['trace'][-1]['action'] if meta['trace'] else -1)
            parent=ActorCritic(features,actions)
            shapes=[array.shape for array in parent.network]
            parent.network=[archive[f'network{i}'] for i in range(6)]
            for array,shape in zip(parent.network,shapes):
                assert array.shape==shape and array.dtype==np.float64 and np.isfinite(array).all()
            for name in ['gamma','reward_scale','reward_version','macro_seconds']:
                setattr(parent,name,meta[name])
            parent.updates=meta['parent_updates']
            policy=cls(parent,331,meta['memory_reset'])
            for i,name in enumerate(NAMES):
                array=archive[f'parameters{i}'];expected=getattr(policy.core,name)
                assert array.shape==expected.shape and array.dtype==np.float64 and np.isfinite(array).all()
                setattr(policy.core,name,array)
            for group in ['m','v']:
                arrays=[archive[f'{group}{i}'] for i in range(6)]
                for array,param in zip(arrays,policy.parameters()):
                    assert array.shape==param.shape and array.dtype==np.float64 and np.isfinite(array).all()
                    if group=='v': assert (array>=0).all()
                setattr(policy,group,arrays)
            for name in ['updates','episodes','attempts']:
                setattr(policy,name,meta[name])
            policy.rng.bit_generator.state=meta['rng']
            hidden=archive['hidden']
            assert hidden.shape==(32,) and hidden.dtype==np.float64 and np.isfinite(hidden).all()
            if not meta['trace']: assert not hidden.any()
            policy.memory=(hidden,meta['previous']);policy.trace=meta['trace']
            return policy


def TorchCore(policy):
    import torch
    class Module(torch.nn.Module):
        def __init__(self):
            super().__init__()
            for i,array in enumerate(policy.core.network):
                self.register_buffer(f'base{i}',torch.tensor(array,dtype=torch.float64))
            self.gru=torch.nn.GRUCell(64+len(policy.actions),32).double()
            with torch.no_grad():
                for name in NAMES[:4]:
                    getattr(self.gru,name).copy_(torch.tensor(getattr(policy.core,name)))
            self.actor=torch.nn.Parameter(torch.tensor(policy.core.actor))
            self.value=torch.nn.Parameter(torch.tensor(policy.core.value))

        def ordered_parameters(self):
            return [getattr(self.gru,name) for name in NAMES[:4]]+[self.actor,self.value]

        def forward(self,states,chosen):
            encoded=torch.tanh(states@self.base0+self.base1)
            hidden=torch.zeros(32,dtype=torch.float64)
            logits,values=[],[]
            for index,state in enumerate(encoded):
                previous=torch.zeros(len(policy.actions),dtype=torch.float64)
                if index:
                    previous[chosen[index-1]]=1
                if policy.memory_reset:
                    hidden=torch.zeros_like(hidden)
                hidden=self.gru(torch.cat([state,previous]),hidden)
                logits.append(state@self.base2+self.base3+hidden@self.actor)
                values.append(state@self.base4+self.base5+hidden@self.value)
            return torch.stack(logits),torch.stack(values)
    return Module()


def update(policy,episodes):
    import torch
    torch.set_num_threads(1)
    for episode in episodes:
        n=len(episode['states']);assert n>0
        assert episode['states'].shape==(n,len(policy.features)) and np.isfinite(episode['states']).all()
        assert episode['legal'].shape==(n,len(policy.actions)) and episode['legal'].dtype==bool
        assert episode['chosen'].shape==(n,) and np.issubdtype(episode['chosen'].dtype,np.integer)
        assert ((episode['chosen']>=0)&(episode['chosen']<len(policy.actions))).all()
        assert episode['legal'][np.arange(n),episode['chosen']].all()
        for name in ['rewards','returns','advantages','values','logp']:
            assert episode[name].shape==(n,) and np.isfinite(episode[name]).all()
        assert episode['terminal'].shape==(n,) and episode['terminal'].dtype==bool
        assert episode['terminal'][-1] and not episode['terminal'][:-1].any()
        returns=discounted_returns(episode['rewards'],policy.gamma)
        np.testing.assert_allclose(episode['returns'],returns,rtol=1e-10,atol=1e-10)
        np.testing.assert_allclose(episode['advantages'],returns-episode['values'],rtol=1e-10,atol=1e-10)
        logits,values=policy.sequence(episode['states'],episode['chosen'])
        old=np.log(probabilities(logits,episode['legal'])[np.arange(len(values)),episode['chosen']])
        np.testing.assert_allclose(old,episode['logp'],rtol=1e-10,atol=1e-10)
        np.testing.assert_allclose(values,episode['values'],rtol=1e-10,atol=1e-10)
    module=TorchCore(policy);params=module.ordered_parameters()
    optimizer=torch.optim.Adam(params,lr=policy.settings['learning_rate'],eps=policy.settings['eps'])
    if policy.updates:
        for p,m,v in zip(params,policy.m,policy.v):
            optimizer.state[p]={'step':torch.tensor(float(policy.updates)),
                                'exp_avg':torch.tensor(m),'exp_avg_sq':torch.tensor(v)}
    advantage=np.concatenate([episode['advantages'] for episode in episodes])
    mean,std=advantage.mean(),max(advantage.std(),1e-8)
    metrics=[]
    for _ in range(policy.settings['epochs']):
        for index in policy.rng.permutation(len(episodes)):
            episode=episodes[index]
            states=torch.tensor(episode['states'],dtype=torch.float64)
            chosen=torch.tensor(episode['chosen'],dtype=torch.int64)
            masks=torch.tensor(episode['legal'])
            old=torch.tensor(episode['logp'])
            adv=torch.tensor((episode['advantages']-mean)/std)
            returns=torch.tensor(episode['returns'])
            logits,values=module(states,chosen)
            distribution=torch.distributions.Categorical(logits=logits.masked_fill(~masks,-torch.inf))
            ratio=torch.exp(distribution.log_prob(chosen)-old)
            actor=-torch.minimum(ratio*adv,ratio.clamp(1-policy.settings['clip'],1+policy.settings['clip'])*adv).mean()
            critic=.5*((values-returns)**2).mean()
            entropy=distribution.entropy().mean()
            loss=actor+policy.settings['value']*critic-policy.settings['entropy']*entropy
            assert torch.isfinite(loss)
            optimizer.zero_grad();loss.backward()
            norm=torch.nn.utils.clip_grad_norm_(params,policy.settings['max_grad_norm'])
            assert torch.isfinite(norm)
            optimizer.step();policy.updates+=1
            metrics.append({'loss':float(loss.detach()),'actor':float(actor.detach()),'critic':float(critic.detach()),
                            'entropy':float(entropy.detach()),'gradient_norm':float(norm.detach())})
    for name,p in zip(NAMES,params):
        setattr(policy.core,name,p.detach().numpy().copy())
    policy.m=[optimizer.state[p]['exp_avg'].numpy().copy() for p in params]
    policy.v=[optimizer.state[p]['exp_avg_sq'].numpy().copy() for p in params]
    policy.episodes+=len(episodes);policy.attempts+=len(episodes)
    return {'updates':len(metrics),'metrics':metrics,'episodes':len(episodes)}
