import unittest
from unittest.mock import patch
import numpy as np
from history_diagnostic import samples, predict, load_archive


class HistoryTests(unittest.TestCase):
    def test_windows_and_targets_stay_inside_training_episode(self):
        states=np.arange(16.)[:, None]
        episode=np.repeat([0,1],8)
        blocks, labels, ids=samples(states,np.arange(16)%2,episode,states,2,(1,2),2)
        for row,label,ep in zip(blocks['ordered'],labels,ids):
            current=int(row[0]); self.assertEqual(int(label[0]),current+2)
            self.assertEqual(current//8,ep)
            self.assertEqual((current-2)//8,ep)
            self.assertEqual((current+2)//8,ep)
            np.testing.assert_array_equal(row.reshape(3,3)[:,0],[current,current-1,current-2])

    def test_shuffled_history_preserves_current_and_past_information(self):
        blocks, _, _=samples(np.arange(16.)[:,None],np.zeros(16,dtype=int),np.zeros(16),np.zeros((16,2)),2,(1,2),2)
        for ordered,shuffled in zip(blocks['ordered'],blocks['shuffled']):
            np.testing.assert_array_equal(ordered[:3],shuffled[:3])
            np.testing.assert_array_equal(np.sort(ordered[3:].reshape(2,3),axis=0),np.sort(shuffled[3:].reshape(2,3),axis=0))

    def test_archive_arrays_are_decompressed_only_once(self):
        class Archive:
            files=['indices','values']
            counts={}
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def __getitem__(self,key):
                self.counts[key]=self.counts.get(key,0)+1
                return np.array([1,2])
        archive=Archive()
        with patch('history_diagnostic.np.load',return_value=archive):
            data=load_archive('unused')
        for _ in range(4):
            np.testing.assert_array_equal(data['indices'],[1,2])
        self.assertEqual(archive.counts,{'indices':1,'values':1})

    def test_predict_fits_only_training_rows(self):
        train=np.arange(20.)[:,None]/20
        expected=2*train+.1
        test=np.array([[.2],[.4]])
        actual=predict(train,expected,test,penalty=0)
        np.testing.assert_allclose(actual,2*test+.1,atol=1e-12)


if __name__=='__main__':
    unittest.main()
