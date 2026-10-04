from types import SimpleNamespace as NS
import unittest
import numpy as np
from src.rl.terran import TerranLearner, FEATURES, ACTIONS, reward
from src.rl.actor_critic import ActorCritic

class CombatEventTests(unittest.TestCase):
    def test_score_counts_minerals_and_gas_across_all_loss_categories(self):
        bot=TerranLearner(ActorCritic(FEATURES,ACTIONS),True,'/tmp/unused')
        fields={f'lost_{resource}_{category}':i+1 for i,category in enumerate(
            ('none','army','economy','technology','upgrade')) for resource in ('minerals','vespene')}
        bot.state=NS(score=NS(killed_value_units=125,killed_value_structures=400,**fields))
        self.assertEqual(bot.combat_score(),{'killed':525,'lost':30})

    def test_each_increment_is_charged_once_to_previous_action(self):
        policy=ActorCritic(FEATURES,ACTIONS);policy.gamma=.9
        bot=TerranLearner(policy,True,'/tmp/unused')
        score={'killed':100,'lost':50};bot.combat_score=lambda:score.copy()
        state=np.zeros(len(FEATURES));mask=np.ones(len(ACTIONS),dtype=bool)
        bot.transition(state,mask,0)
        for killed,lost in [(225,50),(225,50),(225,125)]:
            bot.previous=(state,0,0);bot.decisions.append({'action':'wait'})
            score.update(killed=killed,lost=lost);bot.transition(state,mask,0)
        np.testing.assert_allclose([row[2] for row in bot.transitions],[.0125,0,0])
        self.assertEqual([row['reward_components']['combat_event'] for row in bot.decisions],[1.25,0,0])
        self.assertEqual(bot.decisions[-1]['reward_components']['combat_next']['lost'],125)

    def test_terminal_transition_includes_final_observed_increment_and_win(self):
        policy=ActorCritic(FEATURES,ACTIONS)
        bot=TerranLearner(policy,True,'/tmp/unused')
        state=np.zeros(len(FEATURES));mask=np.ones(len(ACTIONS),dtype=bool)
        bot.combat_score=lambda:{'killed':0,'lost':0};bot.transition(state,mask,8)
        bot.previous=(state,0,8);bot.decisions.append({'action':'attack'})
        bot.combat_score=lambda:{'killed':150,'lost':50}
        bot.transition(state,mask,0,True,100)
        self.assertAlmostEqual(bot.transitions[-1][2],.01*(100+1.5-8))
        self.assertTrue(bot.transitions[-1][-1])

    def test_full_return_contains_discounted_events_in_a_losing_game(self):
        policy=ActorCritic(['state'],['wait']);policy.gamma=.9
        policy.network[5][...]=.3
        potentials=[8,10,9,0];events=[1.25,0,0];transitions=[]
        for i in range(3):
            r=.01*(reward(potentials[i],potentials[i+1],policy.gamma)+events[i])
            transitions.append((np.array([0.]),0,r,np.array([0.]),np.array([True]),i==2))
        policy.collect_episode(transitions,[np.array([True])]*3)
        for i,row in enumerate(policy.rollout):
            expected=-.01*potentials[i]+.01*sum(policy.gamma**(j-i)*events[j] for j in range(i,3))
            self.assertAlmostEqual(row[5],expected)
