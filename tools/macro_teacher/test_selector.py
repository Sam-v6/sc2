import unittest
import numpy as np
from src.rl.terran import ACTIONS,FEATURES,SCALES,encode
from selector import choose


class SelectorTests(unittest.TestCase):
    def pick(self,stats,legal):
        state=encode(stats);mask=np.array([name in legal for name in ACTIONS])
        return ACTIONS[choose(state,mask)]

    def test_supply_and_workers_have_legal_priorities(self):
        self.assertEqual(self.pick({'supply_left':1,'workers':16,'bases':1},['wait','scv','depot']),'depot')
        self.assertEqual(self.pick({'supply_left':8,'workers':16,'bases':1},['wait','scv','depot']),'scv')
        self.assertEqual(self.pick({'supply_left':1,'workers':16,'bases':1},['wait','scv']),'scv')

    def test_army_economy_and_support_requests(self):
        common={'workers':22,'bases':1,'supply_left':20,'barracks':2,'refinery':2,'army':10}
        self.assertEqual(self.pick(common,['wait','marine']),'marine')
        self.assertEqual(self.pick({**common,'army':32},['wait','attack','marine']),'attack')
        self.assertEqual(self.pick({**common,'army':32,'attacking':1},['wait','retreat','marine']),'marine')
        tech={**common,'workers':44,'bases':2,'barracks':4,'factory':1,'starport':1,'army':30,'attacking':1}
        self.assertEqual(self.pick(tech,['wait','medivac','marine']),'medivac')
        self.assertEqual(self.pick({**tech,'medivacs':2},['wait','tank','marine']),'tank')

    def test_nothing_bypasses_legal_mask_or_uses_unused_spatial_features(self):
        rng=np.random.default_rng(77)
        for _ in range(100):
            state=rng.random(len(FEATURES));mask=rng.random(len(ACTIONS))>.6;mask[0]=True
            self.assertTrue(mask[choose(state,mask)])
            altered=state.copy();altered[len(SCALES)+1:]=rng.random(len(altered)-len(SCALES)-1)
            self.assertEqual(choose(state,mask),choose(altered,mask))
        self.assertEqual(self.pick({},['wait']),'wait')


if __name__=='__main__':unittest.main()
