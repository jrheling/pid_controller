#!/usr/bin/python

import time

class PeakState:
    NONE, HIGH, LOW = range(3)

# FIXME
# docstring
    
class PeakCounter(object):
    """ PeakCounter is a list of numbers that is aware of its max, min, and
        number of peaks found.  Peaks are defined within a configurable window
        ("lookback") so that jitter/noise can be ignored where necessary.
        
        It is of arbitary size, so that it can be used to count until a certain
        number of peaks has been found, if desired."""

    # pylint: disable=E0202
    #    (pylint 0.25.1 can't handle property assignment from init - see http://www.logilab.org/ticket/89786)

    
    def __init__(self, max_peaks = 10):
        """docstring for __init__"""
        # config
        self.lookback_size = 5        # arbitrary default - do not assume this is fit for any particular purpose (FIXME)
        self._max_peaks = max_peaks   # current behavior is to ignore peaks > maxPeaks.  FIXME: consider
                                    # note: only settable at construction time
        
        # data
        self._data = []
        
        self._num_peaks = 0
        self._peaks = [None]*self._max_peaks

        # state
        self._just_inflected = False
        self._state = PeakState.NONE
        self._p1_time = None    # time of most recent peak
        self._p2_time = None    # time of 2nd most recent peak


    @property
    def lookback_size(self):
        return self._lookback_size

    @lookback_size.setter
    def lookback_size(self, arg):  
        """LookbackSize determines the minimum number of values needed before
           we can conclude that anything is a peak."""
        try:
            self._lookback_size = int(arg)
        except ValueError:
            raise ValueError("lookback_size must be an int")
        if self._lookback_size <= 1:
            raise ValueError("lookback_size must be at least 2")

    @property
    def num_peaks(self):
        print self._peaks
        if self._peaks[self._num_peaks] is not None:
            if self._state == PeakState.LOW:
                ## low points are put in as a holding place (why?  FIXME?)
                return self._num_peaks
            else:
                return self._num_peaks + 1
        else:
            return self._num_peaks

    @property
    def just_inflected(self):
        """ True iff the last added value was an inflection point."""
        return self._just_inflected
        
    @property
    def last_peak_delta(self):
        """ Difference between the time of the last peak and the one before it. """
        return self._p1_time - self._p2_time
    
    def add_value(self, val):
        is_max = is_min = False   # FIXME - is this where we want to default
        if not isinstance(val, (int, long, float, complex)):
            raise ValueError("PeakCounter can only take numbers")

        ## we compute max/min within the most recent _lookback_size data points
        # print "len(self._data) = %d, lookbackSize = %d" % (len(self._data), self._lookback_size)
        # print "_data = %s" % str(self._data)
        if len(self._data) <= self._lookback_size:
            lookbackwindow = self._data
        else:
            lookbackwindow = self._data[(len(self._data) - self._lookback_size):len(self._data)]
        # print "checking min/max of %f against %s" % (val,str(lookbackwindow))
        if len(self._data):
            if val > max(lookbackwindow):
                print "is max!"
                is_max = True
            if val < min(lookbackwindow):
                print "is min!"
                is_min = True
        else:
            #  this is the first value 
            is_max = True
        
        if is_max:
            print "%f is a max" % val
            if self._state == PeakState.NONE:
                self._state = PeakState.HIGH
            elif self._state == PeakState.LOW:
                self._state = PeakState.HIGH
                self._just_inflected = True
                self._p2_time = self._p1_time
            self._p1_time = time.time()
            # print "adding %f to peak spot %d" % (val, self._num_peaks)
            self._peaks[self._num_peaks] = val
        elif is_min:
            print "%f is a min" % val
            if self._state == PeakState.NONE:
                self._state = PeakState.LOW
            if self._state == PeakState.HIGH:
                self._state = PeakState.LOW
                self._num_peaks += 1
                self._just_inflected = True
            
            if self._num_peaks < self._max_peaks:
                # print "adding %f to peak spot %d" % (val, self._num_peaks)
                self._peaks[self._num_peaks] = val
        
        self._data.append(val)
    
    def get_last_peaks(self, n):
        """ Return the last N peaks identified, or all peaks if n > total peaks. 
        
            NB: returns list, with earliest-detected peaks first"""
        if n > self.num_peaks:
            return self._peaks[:self.num_peaks]
        else:
            return self._peaks[(self.num_peaks - n):self.num_peaks]
        
