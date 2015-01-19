#!/usr/bin/python

import PeakCounter
import unittest
import random
import time

class PeakCounterTest(unittest.TestCase):

    def setUp(self):
        self.PC = PeakCounter.PeakCounter()

    def test_construct(self):
        self.assertIsInstance(self.PC, PeakCounter.PeakCounter)

    def test_initnumpeaks(self):
        self.assertEquals(self.PC.num_peaks,0)

    def test_fivepeaks(self):
        self.PC = PeakCounter.PeakCounter(5)
        self.assertEquals(self.PC._max_peaks,5)
    
    def test_add_value(self):
        """docstring for test_add_value"""
        self.PC.add_value(random.randint(0,100))
    
    def test_set_lookback_sizeNaN(self):
        with self.assertRaises(ValueError):
            self.PC.lookback_size = "foo"
    
    def test_set_lookback_sizeTooSmal(self):
        with self.assertRaises(ValueError):
            self.PC.lookback_size = 1
    
    def test_set_lookback_size(self):
        i = random.randint(2,85)
        self.PC.lookback_size = i
        self.assertEquals(self.PC.lookback_size,i)

    def test_justInflexted(self):
        # FIXME: implement
        pass
        
    def test_get_num_peaks(self):
        # FIXME: implement
        pass
        
    def test_sequence1(self):
        seq = [ 5, 1, 2, 4, 12, 8, 3, 6, 1.5, 4, 5.3, 8.7, 8.6, 0.7]
        # peaks should be 5, 12, 8.7
        for i in seq:
            self.PC.add_value(i)
            time.sleep(0.1)
        self.assertEquals(self.PC.num_peaks,3)
        self.assertEquals(self.PC.get_last_peaks(2),[12, 8.7])
        self.assertEquals(self.PC.get_last_peaks(4),[5, 12, 8.7])
        self.assertEquals(self.PC.get_last_peaks(3),[5, 12, 8.7])
        self.assertEquals(self.PC.get_last_peaks(1),[8.7])
        ## last_peak_delta includes processing time, so we can't predict it precisely
        self.assertTrue((self.PC.last_peak_delta - 0.7) < 0.005)
    pass
    
    

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(PeakCounterTest)
    unittest.TextTestRunner(verbosity=2).run(suite)