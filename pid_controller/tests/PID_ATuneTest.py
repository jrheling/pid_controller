#!/usr/bin/python

import PID_ATune
import unittest
import random

class PID_ATuneTest(unittest.TestCase):
    
    def setUp(self):
        self.PAT = PID_ATune.PID_ATune(None, None)
        
    def test_construct(self):
        self.assertIsInstance(self.PAT, PID_ATune.PID_ATune)
    
    def test_init(self):
        self.assertEquals(self.PAT.control_type, True)
    
    def test_outputstep(self):
        self.PAT.output_step = 3.2
        self.assertEquals(self.PAT.output_step,3.2)

    def test_controltype(self):
        self.PAT.control_type = PID_ATune.ControlType.PID
        self.assertTrue(self.PAT.control_type)
        
    def test_controltypeparam(self):
        with self.assertRaises(TypeError):
            self.PAT.control_type = "foo"
        
    def test_lookbacksec0(self):
        self.PAT.lookback_sec = 0
        self.assertEquals(self.PAT.lookback_sec,1)
        
    def test_lookbacksec10(self):
        self.PAT.lookback_sec = 10
        self.assertEquals(self.PAT.lookback_sec,10)
           
    def test_lookbacksec43(self):
        self.PAT.lookback_sec = 43
        self.assertEquals(self.PAT.lookback_sec,43)

    def test_lookbacksec100(self):
        self.PAT.lookback_sec = 100
        self.assertEquals(self.PAT.lookback_sec,100)
        
    def test_noiseband(self):
        self.PAT.noise_band = 4.6
        self.assertEquals(self.PAT.noise_band, 4.6)

class PID_ATune_StabilityTest(unittest.TestCase):
    """ Test the stability verification method with dummy input/output functions. """
    
    def stable_input_func(self):
        return 5  # arbitrary value
    
    def stable_output_func(self, _):
        return 10 # arbitrary value
    
    def unstable_output_func(self, _):
        if random.randint(1,4) == 2:
            return 9
        else:
            return 10
            
    def test_stable(self):
        self.PAT = PID_ATune.PID_ATune(self.stable_input_func, self.stable_output_func)
        self.assertTrue(self.PAT.verify_stability())
        
    def test_unstable(self):
        self.PAT = PID_ATune.PID_ATune(self.stable_input_func, self.unstable_output_func)
        self.assertRaises(PID_ATune.PIDNotStableError,self.PAT.verify_stability)
        
        
    
if __name__ == '__main__':
    for tcase in PID_ATuneTest, PID_ATune_StabilityTest:
        suite = unittest.TestLoader().loadTestsFromTestCase(tcase)
        unittest.TextTestRunner(verbosity=2).run(suite)

