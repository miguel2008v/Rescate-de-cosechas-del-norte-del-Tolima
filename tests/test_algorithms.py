import unittest
from logic.algorithms import (DEFAULT_PRODUCERS, merge_sort, subset_sum_assignment,
                              solve, route_distance, DEPOT)

class ProjectTests(unittest.TestCase):
    def test_original_data(self):
        result=solve()
        self.assertTrue(result['feasible'])
        self.assertTrue(result['optimal'])
        self.assertEqual(result['exact']['total_load'],180)
        all_ids=[]
        for t in result['exact']['trucks']:
            self.assertLessEqual(t['load'],t['capacity'])
            self.assertEqual(t['route'][0],'D')
            self.assertEqual(t['route'][-1],'D')
            all_ids.extend(t['route'][1:-1])
        self.assertEqual(set(all_ids),{p['id'] for p in DEFAULT_PRODUCERS})
        self.assertEqual(len(all_ids),len(set(all_ids)))
        self.assertLessEqual(result['exact']['total_distance'],result['greedy']['total_distance']+0.0001)
    def test_unfeasible(self):
        result=solve(DEFAULT_PRODUCERS,[60,60])
        self.assertFalse(result['feasible'])
    def test_merge_sort(self):
        data=[{'v':7},{'v':2},{'v':5}]
        self.assertEqual([x['v'] for x in merge_sort(data,lambda p:p['v'])],[2,5,7])
    def test_dp(self):
        assigned=subset_sum_assignment(DEFAULT_PRODUCERS,[100,100])
        self.assertIsNotNone(assigned)
        self.assertEqual(set(assigned[0]+assigned[1]),{p['id'] for p in DEFAULT_PRODUCERS})
    def test_invalid_weights(self):
        data=[dict(x) for x in DEFAULT_PRODUCERS]
        data[0]['weight']=-5
        with self.assertRaises(ValueError):solve(data,[100,100])

if __name__=='__main__': unittest.main()
