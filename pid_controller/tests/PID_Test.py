#!/usr/bin/python

import PID
import unittest
import random

class PID_Test(unittest.TestCase):
    
    def setUp(self):
        self.p = PID.PID()

    def test_construct(self):
        self.assertIsInstance(self.p, PID.PID)
    
    def test_init(self):
        self.assertEquals(self.p.setpoint, 0)
        self.assertEquals(self.p._prev_PV, 0)
            
    # assigning to C{p,i,d} should fail
    def test_assign_to_internal_PID_state(self):
        with self.assertRaises(AttributeError):
             self.p.Cp = 10
             self.p.Ci = 10
             self.p.Cd = 10

    # assignments to manual_override should be clamped to out_min,out_max
    def test_min_max_manual(self):
        self.p.out_min = 5
        self.p.out_max = 10
        # normal case
        self.assertEquals(self.p.manual_override(6),6)
        # clamp to max
        self.assertEquals(self.p.manual_override(15),10)
        # clamp to min
        self.assertEquals(self.p.manual_override(2),5)
            
    # manual_mode assignments work
    def test_manual_mode(self):    
        # regular
        self.p.manual_mode = False
        self.assertFalse(self.p.manual_mode)
        self.p.manual_mode = True
        self.assertTrue(self.p.manual_mode)
        # idempotence
        self.p.manual_mode = False
        self.p.manual_mode = False
        self.assertFalse(self.p.manual_mode)
        self.p.manual_mode = True
        self.p.manual_mode = True
        self.assertTrue(self.p.manual_mode)
        # implicit
        self.p.manual_mode = False
        self.p.manual_override(6)
        self.assertTrue(self.p.manual_mode)
    
    # make sure manual_override returns a value immediately after it's set
    def test_manual_return(self):
        outval = self.p.manual_override(random.randint(1,10))
        self.assertEquals(self.p.manual_override(None), outval)
    
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(PID_Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

